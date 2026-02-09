#!/usr/bin/env python3
"""
TruthTalent API - Version Complète
"""
import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from io import BytesIO

# FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Imports conditionnels
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Notre extracteur de CV
from cv_extractor import cv_extractor

# ========== CONFIGURATION ==========
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cpdokjsyxmohubgvxift.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ========== APPLICATION ==========
app = FastAPI(
    title="TruthTalent CV Parser API",
    description="API d'extraction avancée de CV + intégration Supabase",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SUPABASE MANAGER ==========
class SupabaseManager:
    """Gestionnaire Supabase adapté à votre schéma"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        
        if SUPABASE_AVAILABLE and self.supabase_key:
            self.client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Connexion Supabase établie")
        else:
            self.client = None
            print("⚠️ Supabase non disponible")
    
    def save_candidate(self, cv_data: Dict, file_hash: str, filename: str, 
                      wp_user_id: Optional[int] = None, offer_id: Optional[int] = None) -> Dict:
        """Sauvegarde un candidat dans Supabase selon votre schéma"""
        if not self.client:
            return {"success": False, "error": "Supabase non configuré"}
        
        try:
            # Extraire les données structurées
            extracted = cv_data.get("extracted", {})
            analysis = cv_data.get("analysis", {})
            
            # Préparer les données pour votre table
            candidate_data = {
                "nom": extracted.get("last_name", ""),
                "prenom": extracted.get("first_name", ""),
                "email": extracted.get("email", ""),
                "telephone": extracted.get("phone", ""),
                "adresse": extracted.get("location", ""),
                "competences": self._prepare_json(extracted.get("skills", [])),
                "experiences": self._prepare_json(extracted.get("experience_details", [])),
                "linkedin": extracted.get("linkedin", ""),
                "formations": self._prepare_json(extracted.get("education", [])),
                "langues": self._prepare_json(extracted.get("languages", [])),
                "raw_text": cv_data.get("metadata", {}).get("original_text_preview", "")[:5000],
                "metiers": ", ".join(extracted.get("skills", []))[:200],
                "entreprise": extracted.get("current_company", ""),
                "fichier": filename,
                "postes": extracted.get("current_position", ""),
                "profil": extracted.get("summary", ""),
                "lien": "",
                "niveau": extracted.get("level", "mid-level"),
                "annees_experience": float(extracted.get("years_experience", 0.0)),
                "cv_filename": filename,
                "cv_url": "",
                "file_hash": file_hash,
                "status": "analysé",
                "statut": "analysé",
                "date_import": datetime.now().isoformat(),
                "date_analyse": datetime.now().isoformat(),
                "date_extraction": datetime.now().isoformat(),
                "extraction_date": datetime.now().isoformat(),
                "source": "api_python",
                "parse_status": "success",
                "confidence_score": float(analysis.get("confidence_score", 0.0)),
                "file_type": filename.split('.')[-1] if '.' in filename else "",
                "wp_user_id": wp_user_id,
                "user_id": wp_user_id,
                "user_name": "",
                "wp_offer_id": offer_id,
                "offre_id": offer_id,
                "offre_postulee": offer_id
            }
            
            # Nettoyer les valeurs None
            cleaned_data = {}
            for key, value in candidate_data.items():
                if value is None:
                    cleaned_data[key] = ""
                elif isinstance(value, float):
                    cleaned_data[key] = value
                else:
                    cleaned_data[key] = str(value)
            
            # Vérifier si le candidat existe déjà
            existing_id = self._check_duplicate(file_hash, extracted.get("email"))
            
            if existing_id:
                # Mise à jour
                response = self.client.table("candidats") \
                    .update(cleaned_data) \
                    .eq("id", existing_id) \
                    .execute()
                
                return {
                    "success": True,
                    "action": "updated",
                    "candidate_id": existing_id,
                    "data": response.data[0] if response.data else None
                }
            else:
                # Insertion
                response = self.client.table("candidats") \
                    .insert(cleaned_data) \
                    .execute()
                
                candidate_id = response.data[0]["id"] if response.data else None
                
                return {
                    "success": True,
                    "action": "created",
                    "candidate_id": candidate_id,
                    "data": response.data[0] if response.data else None
                }
                
        except Exception as e:
            print(f"❌ Erreur Supabase: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "error"
            }
    
    def _prepare_json(self, data: Any) -> Optional[str]:
        """Prépare les données pour le stockage JSON"""
        if not data:
            return None
        
        try:
            return json.dumps(data, ensure_ascii=False)
        except:
            return json.dumps(str(data), ensure_ascii=False)
    
    def _check_duplicate(self, file_hash: str, email: str = None) -> Optional[int]:
        """Vérifie si le candidat existe déjà"""
        try:
            # D'abord par file_hash (le plus fiable)
            if file_hash:
                response = self.client.table("candidats") \
                    .select("id") \
                    .eq("file_hash", file_hash) \
                    .execute()
                
                if response.data and len(response.data) > 0:
                    return response.data[0]["id"]
            
            # Ensuite par email
            if email:
                response = self.client.table("candidats") \
                    .select("id") \
                    .eq("email", email) \
                    .execute()
                
                if response.data and len(response.data) > 0:
                    return response.data[0]["id"]
                    
        except Exception as e:
            print(f"⚠️ Erreur vérification doublon: {e}")
        
        return None


# Instance globale
supabase_manager = SupabaseManager()

# ========== ROUTES API ==========
@app.get("/")
async def root():
    """Route racine"""
    return {
        "service": "TruthTalent CV Parser API",
        "version": "2.0.0",
        "status": "online",
        "endpoints": {
            "/extract": "Analyse un CV",
            "/process-wordpress-upload": "Endpoint WordPress",
            "/health": "Vérification santé",
            "/test-supabase": "Test Supabase"
        }
    }

@app.get("/health")
async def health():
    """Vérification de santé"""
    return {
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "operational",
            "extractor": "ready",
            "supabase": "ready" if supabase_manager.client else "disabled"
        }
    }

@app.post("/extract")
async def extract_cv(file: UploadFile = File(...)):
    """
    Analyse un CV et extrait les informations
    
    Args:
        file: Fichier CV (PDF, DOCX, TXT)
    
    Returns:
        Dict: Informations extraites du CV
    """
    try:
        # Validation
        if not file.filename:
            raise HTTPException(400, "Nom de fichier manquant")
        
        # Lire le fichier
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(400, "Fichier vide")
        
        if len(file_content) > 10 * 1024 * 1024:  # 10MB max
            raise HTTPException(400, "Fichier trop volumineux (max 10MB)")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text or len(text.strip()) < 20:
            return JSONResponse({
                "success": True,
                "warning": "Texte insuffisant pour analyse approfondie",
                "extracted": {
                    "filename": file.filename,
                    "size": len(file_content)
                }
            })
        
        # Analyser le CV
        result = cv_extractor.analyze_cv(text, file.filename)
        
        # Calculer le hash du fichier
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase si configuré
        if supabase_manager.client:
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename
            )
            
            if save_result["success"]:
                result["supabase_save"] = save_result
            else:
                result["supabase_save"] = {
                    "success": False,
                    "warning": save_result.get("error", "Erreur inconnue")
                }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur dans /extract: {e}")
        return JSONResponse(
            {"success": False, "error": "Erreur interne du serveur"},
            status_code=500
        )

@app.post("/process-wordpress-upload")
async def process_wordpress_upload(
    file: UploadFile = File(...),
    wp_user_id: Optional[int] = None,
    wp_offer_id: Optional[int] = None,
    message: Optional[str] = None
):
    """
    Endpoint spécial pour les uploads depuis WordPress
    
    Args:
        file: Fichier CV
        wp_user_id: ID utilisateur WordPress
        wp_offer_id: ID offre WordPress
        message: Message de candidature
    
    Returns:
        Dict: Résultat de l'analyse avec format adapté
    """
    try:
        # Validation
        if not file.filename:
            raise HTTPException(400, "Nom de fichier manquant")
        
        # Lire le fichier
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(400, "Fichier vide")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text or len(text.strip()) < 20:
            return {
                "success": True,
                "warning": "Texte insuffisant pour analyse approfondie",
                "extracted": {
                    "filename": file.filename,
                    "email": "",
                    "phone": "",
                    "name": "Candidat",
                    "skills": [],
                    "languages": [],
                    "level": "entry"
                }
            }
        
        # Analyser le CV
        result = cv_extractor.analyze_cv(text, file.filename)
        
        # Calculer le hash
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase
        save_result = {}
        if supabase_manager.client:
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename,
                wp_user_id=wp_user_id,
                offer_id=wp_offer_id
            )
        
        # Formater la réponse pour WordPress
        response = {
            "success": True,
            "message": "CV analysé avec succès",
            "analysis": result.get("analysis", {}),
            "extracted": result.get("extracted", {}),
            "supabase": save_result,
            "file_info": {
                "original_name": file.filename,
                "file_hash": file_hash,
                "size": len(file_content),
                "text_length": len(text)
            }
        }
        
        # Ajouter message si fourni
        if message:
            response["candidate_message"] = message
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur /process-wordpress-upload: {e}")
        return JSONResponse(
            {
                "success": False, 
                "error": str(e),
                "recommendation": "Veuillez réessayer avec un autre fichier"
            },
            status_code=500
        )

@app.get("/test-supabase")
async def test_supabase():
    """Test de connexion à Supabase"""
    if not supabase_manager.client:
        return {"connected": False, "error": "Client Supabase non initialisé"}
    
    try:
        # Test simple
        response = supabase_manager.client.table("candidats").select("count", count="exact").limit(1).execute()
        
        return {
            "connected": True,
            "supabase_url": SUPABASE_URL,
            "table_test": "success" if response.count is not None else "failed",
            "count": response.count
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}

# ========== POINT D'ENTRÉE ==========
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 TruthTalent API v2.0 démarrée sur le port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1
    )