# lib/api/main.py - Version corrigée
import hashlib  # AJOUTÉ en haut
import os
import sys
import json
from datetime import datetime
from typing import Dict, Optional

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Gestion des imports optionnels
try:
    from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️  FastAPI non installé - mode test seulement")

try:
    from supabase_handler import SupabaseHandler
    SUPABASE_HANDLER_AVAILABLE = True
except ImportError as e:
    SUPABASE_HANDLER_AVAILABLE = False
    print(f"⚠️  SupabaseHandler non disponible: {e}")

# Créer l'application seulement si FastAPI est disponible
if FASTAPI_AVAILABLE:
    app = FastAPI(title="TruthTalent API")
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app = None
    print("⚠️  Application FastAPI non créée - installations manquantes")

# Initialiser Supabase
supabase_handler = None
if SUPABASE_HANDLER_AVAILABLE:
    try:
        supabase_handler = SupabaseHandler()
        print("✅ Supabase connecté avec succès")
    except Exception as e:
        print(f"⚠️  Supabase non initialisé: {e}")
else:
    print("⚠️  SupabaseHandler non disponible")

# Routes seulement si app existe
if app:
    @app.get("/")
    async def root():
        return {
            "message": "TruthTalent API opérationnelle",
            "version": "1.0",
            "endpoints": {
                "root": "GET /",
                "health": "GET /health",
                "upload_cv": "POST /jobs",
                "get_candidates": "GET /candidates"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Vérifie la santé de l'API"""
        status = {
            "api": "healthy" if FASTAPI_AVAILABLE else "missing_deps",
            "supabase": "connected" if supabase_handler else "disconnected",
            "deps": {
                "fastapi": FASTAPI_AVAILABLE,
                "supabase_handler": SUPABASE_HANDLER_AVAILABLE
            }
        }
        
        if not FASTAPI_AVAILABLE:
            status["error"] = "Installez: pip install fastapi uvicorn"
        
        return status
    
    @app.post("/jobs")
    async def process_cv_job(
        file: UploadFile = File(...),
        email: str = None
    ):
        """Traite un CV"""
        try:
            # Lire le fichier
            contents = await file.read()
            
            # Calculer le hash
            file_hash = hashlib.md5(contents).hexdigest()
            
            # Sauvegarder dans Supabase Storage
            if supabase_handler:
                bucket_name = "cvs"
                file_path = f"{file_hash}_{file.filename}"
                
                # Upload vers Supabase Storage
                try:
                    storage_response = supabase_handler.client.storage.from_(bucket_name).upload(
                        file_path, contents
                    )
                    
                    # Préparer les données du CV
                    cv_data = {
                        "nom": "À extraire du CV",
                        "prenom": "",
                        "email": email or "inconnu@example.com",
                        "filename": file.filename,
                        "file_hash": file_hash,
                        "raw_text": "Contenu à analyser..."
                    }
                    
                    # Sauvegarder dans la table
                    result = supabase_handler.save_candidate(cv_data, file_hash, file.filename)
                    
                    return {
                        "success": True,
                        "message": "CV traité avec succès",
                        "file_hash": file_hash,
                        "storage_path": file_path,
                        "supabase_result": result
                    }
                    
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Erreur Supabase: {str(e)}")
            else:
                raise HTTPException(status_code=503, detail="Supabase non configuré")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur traitement CV: {str(e)}")
    
    @app.get("/candidates")
    async def get_candidates(limit: int = 50, offset: int = 0):
        """Récupère la liste des candidats"""
        if not supabase_handler:
            raise HTTPException(status_code=503, detail="Supabase non disponible")
        
        result = supabase_handler.get_candidates(limit, offset)
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=500, detail=result['error'])
    
    # Pour le lancement local
    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
else:
    # Mode de secours
    print("\n" + "="*50)
    print("INSTALLATION REQUISE:")
    print("pip install fastapi uvicorn supabase python-dotenv")
    print("="*50 + "\n")