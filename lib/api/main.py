# lib/api/main.py - VERSION CORRIGÉE
import hashlib
import os
import sys
import json
import traceback
import uvicorn
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any 


# ============================================
# CONFIGURATION CORS
# ============================================
app = FastAPI(title="TruthTalent API", version="1.0.0")

# Configuration CORS COMPLÈTE - AUTORISEZ VOTRE DOMAINE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://truthtalent.online",  # Votre site WordPress
        "http://localhost:3000",        # Dev local
        "http://127.0.0.1:3000",        # Dev local
        "https://truthtalent.vercel.app", # Votre app Vercel si différente
        "http://localhost:8000",         # API locale
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Ajoutez aussi un endpoint OPTIONS explicite
@app.options("/{rest_of_path:path}")
async def options_handler(rest_of_path: str):
    return {
        "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allowed_headers": ["*"],
        "allowed_origins": ["https://truthtalent.online"]
    }

# Ajouter le chemin parent pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.join(current_dir, '..')
sys.path.append(parent_dir)

# Gestion des imports optionnels
try:
    from lib.cv_parser import CVParser
    CV_PARSER_AVAILABLE = True
    print("✅ CVParser importé")
except ImportError as e:
    CV_PARSER_AVAILABLE = False
    print(f"⚠️ CVParser non disponible: {e}")

# Import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
    print("✅ Supabase importé")
except ImportError as e:
    SUPABASE_AVAILABLE = False
    print(f"⚠️ Supabase non disponible: {e}")

# ============================================
# PARSER CV MINIMAL SI MANQUANT
# ============================================
if not CV_PARSER_AVAILABLE:
    class CVParser:
        def parse_cv(self, file_content: bytes, filename: str) -> Dict:
            """Parser minimal de secours"""
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
# HANDLER SUPABASE
# ============================================
class SupabaseHandler:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://cpdokjsyxmohubgvxift.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwZG9ranN5eG1vaHViZ3Z4aWZ0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjYzMjUzNCwiZXhwIjoyMDY4MjA4NTM0fQ.j20HSa3F4HezWUwHrKt6Y2p7_ZZV1yOAKO1L3_h2yCM')
        
        print(f"Supabase URL: {self.supabase_url}")
        print(f"Supabase Key length: {len(self.supabase_key) if self.supabase_key else 0}")
        
        if not self.supabase_url or not self.supabase_key:
            print("⚠️ Variables Supabase manquantes dans l'environnement")
            self.client = None
        else:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Client Supabase créé avec succès")
            except Exception as e:
                print(f"❌ Erreur création client Supabase: {e}")
                self.client = None
    
    def upload_to_storage(self, file_content: bytes, file_hash: str, filename: str) -> Dict:
        """Upload un fichier vers Supabase Storage"""
        if not self.client:
            return {"success": False, "error": "Client Supabase non disponible"}
        
        try:
            bucket_name = "cvs"
            file_path = f"{file_hash}_{filename}"
            
            print(f"📤 Tentative d'upload vers bucket '{bucket_name}', chemin: {file_path}")
            
            # Déterminer le content-type
            content_type = "application/octet-stream"
            if filename.lower().endswith('.pdf'):
                content_type = "application/pdf"
            elif filename.lower().endswith('.doc'):
                content_type = "application/msword"
            elif filename.lower().endswith('.docx'):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            # Upload vers Supabase Storage
            response = self.client.storage.from_(bucket_name).upload(
                file_path, 
                file_content,
                {"content-type": content_type}
            )
            
            # Générer l'URL publique
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            
            print(f"✅ Upload réussi: {public_url}")
            
            return {
                "success": True,
                "file_path": file_path,
                "public_url": public_url,
                "bucket": bucket_name
            }
            
        except Exception as e:
            print(f"❌ Erreur upload storage: {e}")
            return {"success": False, "error": str(e)}
    
    def save_candidate(self, cv_data: Dict, file_hash: str, filename: str) -> Dict:
        """Sauvegarder les données du candidat dans la base"""
        if not self.client:
            return {"success": False, "error": "Supabase non disponible"}
        
        try:
            # Préparer le record
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
                'raw_text': cv_data.get('raw_text', '')[:5000],  # Limiter la taille
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
            
            print(f"📝 Sauvegarde candidat: {candidate_record['email']}")
            
            response = self.client.table('candidats').insert(candidate_record).execute()
            
            print(f"✅ Candidat sauvegardé: ID {response.data[0]['id'] if response.data else 'N/A'}")
            
            return {
                "success": True,
                "candidat_id": response.data[0]['id'] if response.data else None,
                "action": "created"
            }
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde candidat: {e}")
            return {"success": False, "error": str(e)}

# ============================================
# INITIALISATION
# ============================================
cv_parser = CVParser() if CV_PARSER_AVAILABLE else CVParser()
supabase_handler = SupabaseHandler()

print("=" * 50)
print("TruthTalent API Initialisée")
print(f"FastAPI: ✅")
print(f"CVParser: {'✅' if CV_PARSER_AVAILABLE else '⚠️ Fallback'}")
print(f"Supabase: {'✅' if supabase_handler.client else '❌'}")
print("=" * 50)

# ============================================
# ROUTES API
# ============================================
@app.get("/")
async def root():
    return {
        "message": "TruthTalent API opérationnelle",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": {
            "fastapi": True,
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

@app.options("/jobs")
async def options_jobs():
    """Gérer les requêtes OPTIONS pour CORS"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "https://truthtalent.online",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.post("/jobs")
async def process_cv(
    request: Request,
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
        print("📥 NOUVELLE REQUÊTE REÇUE /jobs")
        print(f"Method: {request.method}")
        print(f"Headers: {dict(request.headers)}")
        print(f"File: {file.filename}")
        print(f"Content-Type: {file.content_type}")
        print(f"Email: {email}")
        print(f"User ID: {user_id}")
        print(f"User Name: {user_name}")
        print(f"Offer ID: {offer_id}")
        print(f"Source: {source}")
        print("=" * 50)
        
        # Lire le fichier
        contents = await file.read()
        
        # Validation basique
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nom de fichier manquant")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Fichier vide")
        
        if len(contents) > 10 * 1024 * 1024:  # 10MB max
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 10MB)")
        
        # Calcul du hash
        file_hash = hashlib.md5(contents).hexdigest()
        print(f"📊 Hash calculé: {file_hash}")
        
        # Parser le CV
        cv_data = cv_parser.parse_cv(contents, file.filename)
        
        # Priorité à l'email fourni
        if email:
            cv_data['email'] = email
        elif not cv_data.get('email'):
            cv_data['email'] = f"unknown_{file_hash[:8]}@example.com"
        
        # Ajouter les infos supplémentaires
        cv_data['source'] = source
        if user_id:
            cv_data['wp_user_id'] = user_id
        if user_name:
            cv_data['wp_user_name'] = user_name
        if offer_id:
            cv_data['wp_offer_id'] = offer_id
        if message:
            cv_data['message'] = message
        
        print(f"📝 Données CV extraites: {cv_data.get('nom')} {cv_data.get('prenom')}")
        
        # Upload vers Supabase Storage
        storage_result = None
        if supabase_handler.client:
            storage_result = supabase_handler.upload_to_storage(contents, file_hash, file.filename)
        else:
            storage_result = {"success": False, "error": "Supabase non configuré"}
        
        # Sauvegarder dans la base de données
        db_result = None
        if supabase_handler.client and supabase_handler.client is not None:
            db_result = supabase_handler.save_candidate(cv_data, file_hash, file.filename)
        else:
            db_result = {"success": False, "error": "Supabase non configuré"}
        
        # Préparer la réponse
        response_data = {
            "success": True,
            "message": "CV traité avec succès",
            "timestamp": datetime.now().isoformat(),
            "file_hash": file_hash,
            "filename": file.filename,
            "file_size": len(contents),
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
        
        print(f"✅ Traitement terminé pour {cv_data.get('email')}")
        
        return JSONResponse(
            content=response_data,
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "https://truthtalent.online",
                "Access-Control-Allow-Credentials": "true",
            }
        )
            
    except HTTPException as he:
        print(f"❌ HTTPException: {he.detail}")
        raise he
    except Exception as e:
        print(f"💥 Erreur inattendue dans /jobs: {str(e)}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur interne du serveur: {str(e)[:200]}"
        )

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
        print(f"❌ Erreur récupération candidats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Middleware pour loguer les requêtes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📥 {request.method} {request.url.path}")
    
    # Log des headers pour debug CORS
    if request.method in ["POST", "OPTIONS"]:
        print(f"  Origin: {request.headers.get('origin')}")
        print(f"  Access-Control-Request-Method: {request.headers.get('access-control-request-method')}")
    
    response = await call_next(request)
    
    # Ajouter les headers CORS à toutes les réponses
    response.headers["Access-Control-Allow-Origin"] = "https://truthtalent.online"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    print(f"📤 {response.status_code}")
    return response

# Pour exécution locale
if __name__ == "__main__":
    print("🚀 Démarrage de l'API sur http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)