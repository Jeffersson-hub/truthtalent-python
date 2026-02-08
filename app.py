#!/usr/bin/env python3
"""
TruthTalent API - Version Render Complète
"""
import os
import sys
from pathlib import Path

# Ajoute le chemin des libs
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import json
import logging

# Importer tes modules
try:
    from lib.cv_parser import extract_cv_data
    from lib.supabase_handler import save_to_supabase, init_supabase
    from lib.config import Config
    MODULES_LOADED = True
except ImportError as e:
    print(f"⚠️ Module manquant: {e}")
    MODULES_LOADED = False

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application FastAPI
app = FastAPI(
    title="TruthTalent API",
    description="API d'extraction CV - Déployé sur Render",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
origins = os.getenv("ALLOWED_ORIGINS", "https://truthtalent.online").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Routes API
@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "api": "TruthTalent",
        "status": "online",
        "environment": "Render",
        "timestamp": datetime.now().isoformat(),
        "modules": MODULES_LOADED,
        "port": os.getenv("PORT", "8000"),
        "endpoints": [
            {"method": "GET", "path": "/", "description": "Cette page"},
            {"method": "GET", "path": "/health", "description": "Santé de l'API"},
            {"method": "POST", "path": "/extract", "description": "Extraire un CV"},
            {"method": "POST", "path": "/upload", "description": "Upload avec métadonnées"},
            {"method": "GET", "path": "/docs", "description": "Documentation Swagger"}
        ]
    }

@app.get("/health")
async def health():
    """Endpoint de santé"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "TruthTalent API",
        "render": True,
        "python": sys.version.split()[0]
    }

@app.post("/extract")
async def extract_cv(file: UploadFile = File(...)):
    """
    Extrait les informations d'un CV
    ---
    Format: multipart/form-data
    """
    try:
        logger.info(f"📥 Extraction: {file.filename}")
        
        # Validation
        allowed_ext = ['.pdf', '.docx', '.txt']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_ext):
            raise HTTPException(400, f"Format non supporté. Utilisez: {', '.join(allowed_ext)}")
        
        # Lire le fichier
        contents = await file.read()
        
        # Utiliser ton parser existant
        if MODULES_LOADED:
            try:
                result = extract_cv_data(contents, file.filename)
            except Exception as e:
                result = {"error": f"Parser failed: {str(e)}", "raw_text": str(contents[:500])}
        else:
            # Fallback si parser non chargé
            import re
            text = contents.decode('utf-8', errors='ignore')[:1000]
            email = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            result = {
                "email": email[0] if email else None,
                "text_preview": text[:500],
                "note": "Parser module not loaded"
            }
        
        # Sauvegarder dans Supabase si configuré
        save_result = None
        if MODULES_LOADED:
            try:
                save_result = save_to_supabase({
                    "filename": file.filename,
                    "data": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Supabase error: {e}")
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "data": result,
            "saved_to_supabase": save_result.get("success") if save_result else False,
            "timestamp": datetime.now().isoformat(),
            "api_version": "2.0.0"
        })
        
    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}")
        raise HTTPException(500, f"Erreur d'extraction: {str(e)}")

@app.post("/upload")
async def upload_cv(
    file: UploadFile = File(...),
    user_id: str = Form(None),
    email: str = Form(None),
    job_id: str = Form(None)
):
    """
    Upload complet avec métadonnées
    """
    try:
        # Traitement du fichier
        contents = await file.read()
        file_size = len(contents)
        
        # Extraction
        extracted_data = {}
        if MODULES_LOADED:
            extracted_data = extract_cv_data(contents, file.filename)
        
        # Réponse
        response = {
            "success": True,
            "message": "CV uploadé avec succès",
            "metadata": {
                "filename": file.filename,
                "size": file_size,
                "user_id": user_id,
                "email": email,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat()
            },
            "extracted_data": extracted_data,
            "environment": "Render",
            "api_url": f"https://{os.getenv('RENDER_SERVICE_NAME', 'truth-talent-api')}.onrender.com"
        }
        
        return JSONResponse(response)
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, f"Erreur upload: {str(e)}")

@app.get("/test")
async def test_endpoint():
    """Endpoint de test pour vérifier la connexion"""
    return {
        "test": "success",
        "time": datetime.now().isoformat(),
        "render": True,
        "modules": MODULES_LOADED,
        "cors_origins": origins
    }

# Point d'entrée principal pour Render
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logger.info(f"🚀 Démarrage TruthTalent API sur le port {port}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Désactivé en production
        log_level="info"
    )