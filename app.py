#!/usr/bin/env python3
"""
TruthTalent API - Version Ultra Simplifiée
"""
import os
import re
import json
import hashlib
from datetime import datetime
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
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# ========== CONFIGURATION ==========
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cpdokjsyxmohubgvxift.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ========== APPLICATION ==========
app = FastAPI(
    title="TruthTalent CV Parser",
    description="API d'extraction de CV",
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

# ========== CV EXTRACTOR ULTRA SIMPLE ==========
class SimpleCVExtractor:
    """Extracteur de CV simple"""
    
    def __init__(self):
        self.skills_list = [
            "Python", "Java", "C#", "PHP", "Ruby", "Node.js", "JavaScript",
            "TypeScript", "React", "Vue.js", "Angular", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "SQL", "PostgreSQL", "MySQL", "MongoDB",
            "Git", "Linux", "HTML", "CSS", "REST", "API"
        ]
    
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
            print(f"Warning: {e}")
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
            return ""
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extrait le texte d'un document Word"""
        try:
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            return ""
    
    def analyze_cv(self, text: str, filename: str = "") -> dict:
        """Analyse un CV"""
        # Extraire les informations
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        name = self._extract_name(text)
        skills = self._extract_skills(text)
        
        # Calculer le score de confiance
        confidence = 0.0
        if email:
            confidence += 0.4
        if phone:
            confidence += 0.3
        if name and name != "Candidat":
            confidence += 0.3
        
        return {
            "success": True,
            "analysis": {
                "confidence_score": confidence,
                "processing_date": datetime.now().isoformat()
            },
            "extracted": {
                "name": name,
                "email": email,
                "phone": phone,
                "skills": skills,
                "summary": text[:200] + ("..." if len(text) > 200 else "")
            },
            "metadata": {
                "filename": filename,
                "char_count": len(text)
            }
        }
    
    def _extract_email(self, text: str) -> str:
        """Extrait l'email"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else ""
    
    def _extract_phone(self, text: str) -> str:
        """Extrait le téléphone"""
        phone_patterns = [
            r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}',
            r'\b0[1-9](?:[\s.-]?\d{2}){4}\b'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text.replace(' ', ''))
            if matches:
                return matches[0]
        return ""
    
    def _extract_name(self, text: str) -> str:
        """Extrait le nom"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:3]:
            if 3 < len(line) < 50:
                if not any(word in line.lower() for word in ['email', 'phone', 'tel', 'cv', 'resume', '@']):
                    return line
        return "Candidat"
    
    def _extract_skills(self, text: str) -> list:
        """Extrait les compétences"""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.skills_list:
            if skill.lower() in text_lower and skill not in found_skills:
                found_skills.append(skill)
        
        return found_skills[:10]

# Instance globale
cv_extractor = SimpleCVExtractor()

# ========== SUPABASE MANAGER ==========
class SupabaseManager:
    """Gestionnaire Supabase simplifié"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        
        if SUPABASE_AVAILABLE and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabase connected")
            except Exception as e:
                print(f"⚠️ Supabase error: {e}")
                self.client = None
        else:
            self.client = None
            print("⚠️ Supabase not configured")
    
    def save_candidate(self, cv_data: dict, file_hash: str, filename: str) -> dict:
        """Sauvegarde un candidat"""
        if not self.client:
            return {"success": False, "error": "Supabase not available"}
        
        try:
            extracted = cv_data.get("extracted", {})
            
            candidate_data = {
                "nom": extracted.get("name", ""),
                "email": extracted.get("email", ""),
                "telephone": extracted.get("phone", ""),
                "competences": json.dumps(extracted.get("skills", []), ensure_ascii=False),
                "raw_text": extracted.get("summary", ""),
                "fichier": filename,
                "cv_filename": filename,
                "file_hash": file_hash,
                "status": "analysé",
                "statut": "analysé",
                "date_import": datetime.now().isoformat(),
                "date_analyse": datetime.now().isoformat(),
                "source": "api",
                "parse_status": "success",
                "confidence_score": cv_data.get("analysis", {}).get("confidence_score", 0.0)
            }
            
            response = self.client.table("candidats").insert(candidate_data).execute()
            
            if response.data:
                return {
                    "success": True,
                    "candidate_id": response.data[0].get("id"),
                    "action": "created"
                }
            else:
                return {"success": False, "error": "No data returned"}
                
        except Exception as e:
            print(f"❌ Supabase error: {e}")
            return {"success": False, "error": str(e)}

# Instance globale
supabase_manager = SupabaseManager()

# ========== ROUTES API ==========
@app.get("/")
async def root():
    return {
        "service": "TruthTalent CV Parser",
        "version": "2.0.0",
        "status": "online",
        "endpoints": ["/health", "/extract", "/process-wordpress-upload"]
    }

@app.get("/health")
async def health():
    return {
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "supabase": "connected" if supabase_manager.client else "disabled"
    }

@app.post("/extract")
async def extract_cv(file: UploadFile = File(...)):
    """Analyse un CV"""
    try:
        if not file.filename:
            raise HTTPException(400, "Filename required")
        
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(400, "Empty file")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text or len(text.strip()) < 10:
            return {
                "success": True,
                "warning": "Insufficient text for analysis",
                "extracted": {"filename": file.filename}
            }
        
        # Analyser le CV
        result = cv_extractor.analyze_cv(text, file.filename)
        
        # Calculer le hash
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase
        if supabase_manager.client:
            save_result = supabase_manager.save_candidate(result, file_hash, file.filename)
            result["supabase"] = save_result
        
        return result
        
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/process-wordpress-upload")
async def process_wordpress_upload(
    file: UploadFile = File(...),
    wp_user_id: int = 0,
    wp_offer_id: int = 0,
    message: str = ""
):
    """Endpoint pour WordPress"""
    try:
        if not file.filename:
            raise HTTPException(400, "Filename required")
        
        file_content = await file.read()
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text:
            return {
                "success": True,
                "warning": "No text extracted",
                "extracted": {
                    "name": "Candidat",
                    "email": "",
                    "phone": "",
                    "skills": []
                }
            }
        
        # Analyser
        result = cv_extractor.analyze_cv(text, file.filename)
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder avec infos WordPress
        if supabase_manager.client:
            extracted = result.get("extracted", {})
            
            candidate_data = {
                "nom": extracted.get("name", ""),
                "email": extracted.get("email", ""),
                "telephone": extracted.get("phone", ""),
                "competences": json.dumps(extracted.get("skills", []), ensure_ascii=False),
                "raw_text": extracted.get("summary", ""),
                "fichier": file.filename,
                "cv_filename": file.filename,
                "file_hash": file_hash,
                "status": "analysé",
                "statut": "analysé",
                "date_import": datetime.now().isoformat(),
                "date_analyse": datetime.now().isoformat(),
                "source": "wordpress",
                "parse_status": "success",
                "confidence_score": result.get("analysis", {}).get("confidence_score", 0.0),
                "wp_user_id": wp_user_id,
                "wp_offer_id": wp_offer_id
            }
            
            if message:
                candidate_data["message_candidature"] = message
            
            supabase_manager.client.table("candidats").insert(candidate_data).execute()
        
        return {
            "success": True,
            "message": "CV processed successfully",
            "analysis": result.get("analysis", {}),
            "extracted": result.get("extracted", {}),
            "file_hash": file_hash
        }
        
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

# ========== POINT D'ENTRÉE ==========
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 TruthTalent API started on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1
    )