#!/usr/bin/env python3
"""
TruthTalent API - Version Simplifiée sans spaCy
"""
import os
import re
import json
import hashlib
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
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# ========== CONFIGURATION ==========
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cpdokjsyxmohubgvxift.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ========== APPLICATION ==========
app = FastAPI(
    title="TruthTalent CV Parser API",
    description="API d'extraction de CV + Supabase",
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

# ========== CV EXTRACTOR SIMPLIFIÉ ==========
class SimpleCVExtractor:
    """Extracteur de CV simplifié sans NLP"""
    
    def __init__(self):
        self.skills_database = self._load_skills_database()
        self.french_cities = [
            "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
            "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes"
        ]
    
    def _load_skills_database(self) -> Dict[str, List[str]]:
        """Base de données de compétences"""
        return {
            "backend": ["Python", "Java", "C#", "PHP", "Ruby", "Node.js", "Go", "Rust"],
            "frontend": ["JavaScript", "TypeScript", "React", "Vue.js", "Angular", "Svelte"],
            "devops": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform"],
            "mobile": ["Swift", "Kotlin", "Flutter", "React Native"],
            "database": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis"],
            "data": ["Python", "R", "TensorFlow", "PyTorch", "Pandas", "NumPy"],
            "design": ["Figma", "Adobe XD", "Sketch", "Photoshop"],
            "management": ["Jira", "Confluence", "Trello", "Notion"],
            "soft_skills": ["Communication", "Leadership", "Teamwork"]
        }
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extrait le texte selon le format"""
        filename_lower = filename.lower()
        
        try:
            if filename_lower.endswith('.pdf') and PDF_AVAILABLE:
                return self._extract_pdf_text(file_content)
            elif filename_lower.endswith(('.doc', '.docx')) and DOCX_AVAILABLE:
                return self._extract_docx_text(file_content)
            elif filename_lower.endswith(('.txt', '.rtf')):
                return file_content.decode('utf-8', errors='ignore')
            else:
                return f"[Fichier: {filename}]"
                
        except Exception as e:
            print(f"⚠️ Erreur extraction: {e}")
            return ""
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extrait le texte d'un PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            return f"PDF (erreur: {str(e)[:100]})"
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extrait le texte d'un document Word"""
        try:
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            return f"DOCX (erreur: {str(e)[:100]})"
    
    def analyze_cv(self, text: str, filename: str = "") -> Dict[str, Any]:
        """Analyse un CV"""
        # Nettoyer le texte
        clean_text = self._clean_text(text)
        
        # Extraire les informations
        personal_info = self._extract_personal_info(clean_text)
        skills = self._extract_skills(clean_text)
        languages = self._extract_languages(clean_text)
        
        # Calculer le score de confiance
        confidence_score = self._calculate_confidence({
            "personal_info": personal_info,
            "skills": skills,
            "languages": languages
        })
        
        # Préparer le résultat
        return {
            "success": True,
            "analysis": {
                "confidence_score": confidence_score,
                "processing_date": datetime.now().isoformat(),
                "char_count": len(text),
                "word_count": len(text.split()),
                "parser_version": "1.0"
            },
            "extracted": {
                "name": personal_info.get("name", ""),
                "email": personal_info.get("email", ""),
                "phone": personal_info.get("phone", ""),
                "location": personal_info.get("location", ""),
                "linkedin": personal_info.get("linkedin", ""),
                "skills": skills,
                "languages": languages,
                "summary": self._extract_summary(clean_text)
            },
            "metadata": {
                "filename": filename,
                "original_text_preview": text[:500] + ("..." if len(text) > 500 else ""),
                "has_email": bool(personal_info.get("email")),
                "has_phone": bool(personal_info.get("phone")),
                "has_name": bool(personal_info.get("name"))
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def _extract_personal_info(self, text: str) -> Dict[str, str]:
        """Extrait les informations personnelles"""
        info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": ""
        }
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            info["email"] = emails[0]
        
        # Téléphone français
        phone_patterns = [
            r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}',
            r'\b0[1-9](?:[\s.-]?\d{2}){4}\b'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text.replace(' ', ''))
            if matches:
                info["phone"] = matches[0]
                break
        
        # LinkedIn
        linkedin_pattern = r'(?:linkedin\.com/(?:in|company)/[a-zA-Z0-9-]+)'
        matches = re.findall(linkedin_pattern, text)
        if matches:
            info["linkedin"] = f"https://{matches[0]}"
        
        # Localisation
        for city in self.french_cities:
            if city in text:
                info["location"] = city
                break
        
        # Nom (première ligne significative)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:5]:
            if 3 < len(line) < 50:
                if not any(word in line.lower() for word in ['email', 'phone', 'tel', 'cv', 'resume', '@']):
                    info["name"] = line
                    break
        
        return info
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extrait les compétences"""
        found_skills = []
        text_lower = text.lower()
        
        for category, skills in self.skills_database.items():
            for skill in skills:
                if skill.lower() in text_lower and skill not in found_skills:
                    found_skills.append(skill)
        
        return found_skills[:15]
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extrait les langues"""
        languages = []
        common_languages = [
            "français", "anglais", "espagnol", "allemand", "italien", 
            "portugais", "néerlandais", "chinois", "japonais"
        ]
        
        text_lower = text.lower()
        for lang in common_languages:
            if lang in text_lower:
                languages.append(lang.capitalize())
        
        return list(set(languages))
    
    def _extract_summary(self, text: str) -> str:
        """Extrait un résumé"""
        # Prendre les premières phrases significatives
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if 5 <= len(sentence.split()) <= 30:
                return sentence[:200]
        
        return ""
    
    def _calculate_confidence(self, data: Dict) -> float:
        """Calcule un score de confiance"""
        score = 0.0
        
        if data["personal_info"].get("email"):
            score += 0.3
        if data["personal_info"].get("phone"):
            score += 0.25
        if data["personal_info"].get("name"):
            score += 0.25
        if data["skills"]:
            score += 0.2
        
        return min(score, 1.0)

# Instance globale
cv_extractor = SimpleCVExtractor()

# ========== SUPABASE MANAGER ==========
class SupabaseManager:
    """Gestionnaire Supabase"""
    
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
        """Sauvegarde un candidat"""
        if not self.client:
            return {"success": False, "error": "Supabase non configuré"}
        
        try:
            extracted = cv_data.get("extracted", {})
            
            candidate_data = {
                "nom": extracted.get("name", ""),
                "email": extracted.get("email", ""),
                "telephone": extracted.get("phone", ""),
                "adresse": extracted.get("location", ""),
                "competences": json.dumps(extracted.get("skills", []), ensure_ascii=False),
                "linkedin": extracted.get("linkedin", ""),
                "langues": json.dumps(extracted.get("languages", []), ensure_ascii=False),
                "raw_text": cv_data.get("metadata", {}).get("original_text_preview", "")[:5000],
                "profil": extracted.get("summary", ""),
                "fichier": filename,
                "cv_filename": filename,
                "cv_url": "",
                "file_hash": file_hash,
                "status": "analysé",
                "statut": "analysé",
                "date_import": datetime.now().isoformat(),
                "date_analyse": datetime.now().isoformat(),
                "source": "api_simple",
                "parse_status": "success",
                "confidence_score": cv_data.get("analysis", {}).get("confidence_score", 0.0),
                "file_type": filename.split('.')[-1] if '.' in filename else "",
                "wp_user_id": wp_user_id,
                "user_id": wp_user_id,
                "wp_offer_id": offer_id,
                "offre_id": offer_id
            }
            
            # Insérer
            response = self.client.table("candidats").insert(candidate_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "candidate_id": response.data[0].get("id"),
                    "action": "created"
                }
            else:
                return {"success": False, "error": "Aucune donnée retournée"}
                
        except Exception as e:
            print(f"❌ Erreur Supabase: {e}")
            return {"success": False, "error": str(e)}

# Instance globale
supabase_manager = SupabaseManager()

# ========== ROUTES API ==========
@app.get("/")
async def root():
    return {
        "service": "TruthTalent CV Parser API",
        "version": "2.0.0",
        "status": "online",
        "features": {
            "pdf_parsing": PDF_AVAILABLE,
            "docx_parsing": DOCX_AVAILABLE,
            "supabase": SUPABASE_AVAILABLE and bool(SUPABASE_KEY)
        }
    }

@app.get("/health")
async def health():
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
    """Analyse un CV"""
    try:
        if not file.filename:
            raise HTTPException(400, "Nom de fichier manquant")
        
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(400, "Fichier vide")
        
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(400, "Fichier trop volumineux (max 10MB)")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text or len(text.strip()) < 20:
            return JSONResponse({
                "success": True,
                "warning": "Texte insuffisant pour analyse",
                "extracted": {"filename": file.filename}
            })
        
        # Analyser le CV
        result = cv_extractor.analyze_cv(text, file.filename)
        
        # Calculer le hash
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase
        if supabase_manager.client:
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename
            )
            
            if save_result["success"]:
                result["supabase_save"] = save_result
            else:
                result["supabase_save"] = {"success": False, "warning": save_result.get("error")}
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return JSONResponse(
            {"success": False, "error": "Erreur interne"},
            status_code=500
        )

@app.post("/process-wordpress-upload")
async def process_wordpress_upload(
    file: UploadFile = File(...),
    wp_user_id: Optional[int] = None,
    wp_offer_id: Optional[int] = None,
    message: Optional[str] = None
):
    """Endpoint WordPress"""
    try:
        if not file.filename:
            raise HTTPException(400, "Nom de fichier manquant")
        
        file_content = await file.read()
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text or len(text.strip()) < 20:
            return {
                "success": True,
                "warning": "Texte insuffisant",
                "extracted": {
                    "filename": file.filename,
                    "name": "Candidat",
                    "email": "",
                    "phone": "",
                    "skills": []
                }
            }
        
        # Analyser
        result = cv_extractor.analyze_cv(text, file.filename)
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder
        save_result = {}
        if supabase_manager.client:
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename,
                wp_user_id=wp_user_id,
                offer_id=wp_offer_id
            )
        
        response = {
            "success": True,
            "message": "CV analysé avec succès",
            "analysis": result.get("analysis", {}),
            "extracted": result.get("extracted", {}),
            "supabase": save_result,
            "file_info": {
                "original_name": file.filename,
                "file_hash": file_hash,
                "size": len(file_content)
            }
        }
        
        if message:
            response["candidate_message"] = message
        
        return response
        
    except Exception as e:
        print(f"❌ Erreur WordPress: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/test-supabase")
async def test_supabase():
    """Test Supabase"""
    if not supabase_manager.client:
        return {"connected": False, "error": "Client non initialisé"}
    
    try:
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
    print(f"🚀 TruthTalent API démarrée sur le port {port}")
    print(f"📦 PDF support: {PDF_AVAILABLE}")
    print(f"📄 DOCX support: {DOCX_AVAILABLE}")
    print(f"📊 Supabase: {SUPABASE_AVAILABLE and bool(SUPABASE_KEY)}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1
    )