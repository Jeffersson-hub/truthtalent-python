import hashlib
import os
import sys
import json
from urllib import request
import uvicorn
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, HTTPException, UploadFile, Form
from fastapi import Request


# Créer l'application
app = FastAPI(title="TruthTalent API", version="1.0.0")

# Configuration CORS COMPLÈTE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://truthtalent.online",  # Votre site WordPress
        "http://localhost:3000",        # Dev local
        "http://127.0.0.1:3000",        # Dev local
    ],
    allow_credentials=True,
    allow_methods=["*"],  # GET, POST, etc.
    allow_headers=["*"],  # Tous les headers
    expose_headers=["*"],  # Exposer tous les headers
    max_age=3600,  # Cache CORS pour 1 heure
)

# Ajouter le chemin parent pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
sys.path.append(parent_dir)

# Gestion des imports optionnels
try:
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
    print("✅ FastAPI importé avec succès")
except ImportError as e:
    FASTAPI_AVAILABLE = False
    print(f"⚠️ FastAPI non disponible: {e}")

# Import de votre parser CV
try:
    from lib.cv_parser import CVParser
    CV_PARSER_AVAILABLE = True
    print("✅ CVParser importé")
except ImportError:
    CV_PARSER_AVAILABLE = False
    print("⚠️ CVParser non disponible - création minimaliste")

# Import Supabase
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
    print("✅ Supabase importé")
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase non disponible")

# ============================================
# PARSER CV MINIMAL SI MANQUANT
# ============================================
if not CV_PARSER_AVAILABLE:
    class CVParser:
        def parse_cv(self, file_content: bytes, filename: str) -> Dict:
            return {
                "success": True,
                "raw_text": "Texte extrait minimal",
                "nom": "Test",
                "prenom": "User",
                "email": "test@example.com",
                "telephone": "",
                "competences": ["Python", "JavaScript"],
                "niveau": "Junior",
                "annees_experience": 1.0,
                "confidence_score": 0.5,
                "parse_status": "fallback"
            }

# ============================================
# HANDLER SUPABASE MINIMAL SI MANQUANT
# ============================================
class SupabaseHandler:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY', '')
        
        if not self.supabase_url or not self.supabase_key:
            print("⚠️ Variables Supabase manquantes")
            self.client = None
        else:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Client Supabase créé")
            except Exception as e:
                print(f"❌ Erreur Supabase: {e}")
                self.client = None
    
    def upload_to_storage(self, file_content: bytes, file_hash: str, filename: str) -> Dict:
        if not self.client:
            return {"success": False, "error": "Client Supabase non disponible"}
        
        try:
            bucket_name = "cvs"
            file_path = f"{file_hash}_{filename}"
            
            response = self.client.storage.from_(bucket_name).upload(
                file_path, 
                file_content,
                {"content-type": "application/pdf"}
            )
            
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "public_url": public_url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_candidate(self, cv_data: Dict, file_hash: str, filename: str) -> Dict:
        if not self.client:
            return {"success": False, "error": "Supabase non disponible"}
        
        try:
            candidate_record = {
                'nom': cv_data.get('nom', ''),
                'prenom': cv_data.get('prenom', ''),
                'email': cv_data.get('email', ''),
                'telephone': cv_data.get('telephone', ''),
                'competences': json.dumps(cv_data.get('competences', []), ensure_ascii=False),
                'niveau': cv_data.get('niveau', ''),
                'annees_experience': cv_data.get('annees_experience', 0.0),
                'fichier': filename,
                'file_hash': file_hash,
                'cv_filename': filename,
                'raw_text': cv_data.get('raw_text', '')[:5000],
                'confidence_score': cv_data.get('confidence_score', 0.5),
                'parse_status': cv_data.get('parse_status', 'success'),
                'date_import': datetime.now().isoformat(),
                'source': cv_data.get('source', 'api_python')
            }
            
            # Si WordPress
            if 'wp_user_id' in cv_data:
                candidate_record['wp_user_id'] = cv_data['wp_user_id']
                candidate_record['wp_offer_id'] = cv_data.get('wp_offer_id')
                candidate_record['source'] = 'wordpress'
            
            response = self.client.table('candidats').insert(candidate_record).execute()
            
            return {
                "success": True,
                "candidat_id": response.data[0]['id'] if response.data else None,
                "action": "created"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# ============================================
# CRÉATION DE L'APPLICATION FASTAPI
# ============================================
if FASTAPI_AVAILABLE:
    app = FastAPI(title="TruthTalent API", version="1.0.0")
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Fallback si FastAPI n'est pas installé
    app = None
    print("❌ FastAPI non disponible - application non créée")

# ============================================
# INITIALISATION
# ============================================
cv_parser = CVParser() if CV_PARSER_AVAILABLE else CVParser()
supabase_handler = SupabaseHandler()

print("=" * 50)
print("TruthTalent API Initialisée")
print(f"FastAPI: {'✅' if FASTAPI_AVAILABLE else '❌'}")
print(f"CVParser: {'✅' if CV_PARSER_AVAILABLE else '⚠️ Fallback'}")
print(f"Supabase: {'✅' if supabase_handler.client else '❌'}")
print("=" * 50)

# ============================================
# ROUTES API
# ============================================
if app:
    @app.get("/")
    async def root():
        return {
            "message": "TruthTalent API opérationnelle",
            "version": "1.0.0",
            "status": {
                "fastapi": FASTAPI_AVAILABLE,
                "supabase": supabase_handler.client is not None,
                "cv_parser": CV_PARSER_AVAILABLE
            },
            "endpoints": {
                "root": "GET /",
                "health": "GET /health",
                "upload_cv": "POST /jobs",
                "get_candidates": "GET /candidates"
            }
        }
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "running",
                "supabase": "connected" if supabase_handler.client else "disconnected",
                "cv_parser": "available" if CV_PARSER_AVAILABLE else "fallback"
            }
        }
    
    @app.post("/jobs")
    async def process_cv(
        file: UploadFile = File(...),
        email: Optional[str] = Form(None),
        user_id: Optional[str] = Form(None),
        user_name: Optional[str] = Form(None),
        offer_id: Optional[str] = Form(None),
        message: Optional[str] = Form(None),
        source: str = Form("web")
    ):
        """Endpoint principal pour traiter les CVs"""
        try:
            # Lire le fichier
            contents = await file.read()
            
            # Validation
            if not file.filename.lower().endswith(('.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg')):
                raise HTTPException(status_code=400, detail="Type de fichier non supporté")
            
            # Calcul du hash
            file_hash = hashlib.md5(contents).hexdigest()
            print(f"📄 Fichier reçu: {file.filename} ({len(contents)} bytes)")
            print(f"📧 Email: {email}")
            print(f"👤 User ID: {user_id}")
            print(f"🎯 Offer ID: {offer_id}")
            
            # Parser le CV
            cv_data = cv_parser.parse_cv(contents, file.filename)
            
            # Priorité à l'email fourni
            if email:
                cv_data['email'] = email
            
            # Ajouter les infos WordPress
            cv_data['source'] = source
            if user_id:
                cv_data['wp_user_id'] = user_id
            if user_name:
                cv_data['wp_user_name'] = user_name
            if offer_id:
                cv_data['wp_offer_id'] = offer_id
            if message:
                cv_data['message'] = message
            
            # Upload vers Supabase Storage
            storage_result = None
            if supabase_handler.client:
                storage_result = supabase_handler.upload_to_storage(contents, file_hash, file.filename)
                
                if storage_result.get('success'):
                    print(f"✅ CV uploadé: {storage_result.get('public_url')}")
                else:
                    print(f"⚠️ Upload storage échoué: {storage_result.get('error')}")
            
            # Sauvegarder dans la base de données
            db_result = None
            if supabase_handler.client:
                db_result = supabase_handler.save_candidate(cv_data, file_hash, file.filename)
                
                if db_result.get('success'):
                    print(f"✅ Candidat enregistré: ID {db_result.get('candidat_id')}")
                else:
                    print(f"⚠️ Sauvegarde DB échouée: {db_result.get('error')}")
            
            # Réponse
            response_data = {
                "success": True,
                "message": "CV traité avec succès",
                "file_hash": file_hash,
                "filename": file.filename,
                "cv_data": {
                    "nom": cv_data.get('nom'),
                    "prenom": cv_data.get('prenom'),
                    "email": cv_data.get('email'),
                    "telephone": cv_data.get('telephone'),
                    "competences": cv_data.get('competences', []),
                    "niveau": cv_data.get('niveau'),
                    "annees_experience": cv_data.get('annees_experience'),
                    "confidence_score": cv_data.get('confidence_score', 0.5)
                },
                "storage": storage_result,
                "database": db_result
            }
            
            return JSONResponse(content=response_data, status_code=200)
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"💥 Erreur traitement: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
    
    @app.get("/candidates")
    async def get_candidates(limit: int = 50, offset: int = 0):
        """Récupérer la liste des candidats"""
        if not supabase_handler.client:
            raise HTTPException(status_code=503, detail="Supabase non disponible")
        
        try:
            response = supabase_handler.client.table('candidats') \
                .select('*') \
                .order('date_import', desc=True) \
                .range(offset, offset + limit - 1) \
                .execute()
            
            return {
                "success": True,
                "count": len(response.data),
                "candidates": response.data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # Middleware pour loguer les requêtes
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        print(f"📥 {request.method} {request.url}")
        response = await call_next(request)
        print(f"📤 {response.status_code}")
        return response
    
    # Pour exécution locale
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    @app.post("/jobs")
    async def process_cv(
    file: UploadFile = File(...),
    email: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    user_name: Optional[str] = Form(None),
    offer_id: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    source: str = Form("web")
):
        """Endpoint principal pour traiter les CVs"""
        try:
            print("=" * 50)
            print("📥 NOUVELLE REQUÊTE REÇUE")
            print(f"Headers: {dict(request.headers) if hasattr(request, 'headers') else 'No headers'}")
            print(f"File: {file.filename} ({file.size if hasattr(file, 'size') else 'unknown'} bytes)")
            print(f"Email: {email}")
            print(f"User ID: {user_id}")
            print("=" * 50)
            
            # Lire le fichier
            contents = await file.read()
            print(f"✅ Fichier lu: {len(contents)} bytes")
            
            # Validation
            if not file.filename:
                raise HTTPException(status_code=400, detail="Nom de fichier manquant")
                
            if len(contents) == 0:
                raise HTTPException(status_code=400, detail="Fichier vide")
            
            # Calcul du hash
            import hashlib
            file_hash = hashlib.md5(contents).hexdigest()
            print(f"📊 Hash calculé: {file_hash}")
            
            # Parser le CV (version simplifiée pour test)
            cv_data = {
                "nom": "Test",
                "prenom": "User",
                "email": email or "test@example.com",
                "telephone": "",
                "competences": ["Python", "JavaScript"],
                "niveau": "Junior",
                "annees_experience": 1.0,
                "raw_text": "CV de test",
                "confidence_score": 0.5,
                "parse_status": "test"
            }
            
            print(f"📝 Données CV préparées: {cv_data}")
            
            # Réponse de test
            response_data = {
                "success": True,
                "message": "CV reçu avec succès (mode test)",
                "file_hash": file_hash,
                "filename": file.filename,
                "cv_data": cv_data,
                "test_mode": True
            }
            
            print(f"✅ Réponse envoyée: {response_data}")
            return JSONResponse(content=response_data, status_code=200)
                
        except HTTPException as he:
            print(f"❌ HTTPException: {he.detail}")
            raise he
        except Exception as e:
            print(f"💥 Erreur inattendue: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500, 
                detail=f"Erreur interne: {str(e)[:100]}"
            )
        @app.post("/upload/")
        async def upload_file(
            request: Request,
            file: UploadFile,
            email: str = Form(...),
            user_id: str = Form(...)
        ):
            print("=" * 50)
            print(" NOUVELLE REQUÊTE REÇUE")
            print(f"Headers: {dict(request.headers)}")
            print(f"File: {file.filename} ({file.size})")
            print(f"Email: {email}")
            print(f"User ID: {user_id}")
            print("=" * 50)

            # Lire le fichier
            if file:
                contents = await file.read()
                print(f"✓ Fichier lu: {len(contents)} bytes")
            
            # Validation
            if not file.filename:
                raise HTTPException(status_code=400, detail="Nom de fichier manquant")
            
            return {"message": "Fichier reçu avec succès"}

        if __name__ == "__main__":
            uvicorn.run(app, host="0.0.0.0", port=8000)