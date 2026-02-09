#!/usr/bin/env python3
"""
TruthTalent API - Version CORRIGÉE pour Supabase
"""
import os
import re
import json
import hashlib
from datetime import datetime
from io import BytesIO

# FastAPI
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
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

# ========== CV EXTRACTOR AMÉLIORÉ ==========
class CVExtractor:
    """Extracteur de CV amélioré"""
    
    def __init__(self):
        self.skills_list = [
            "Python", "Java", "C#", "PHP", "Ruby", "Node.js", "JavaScript",
            "TypeScript", "React", "Vue.js", "Angular", "Docker", "Kubernetes",
            "AWS", "Azure", "GCP", "SQL", "PostgreSQL", "MySQL", "MongoDB",
            "Git", "Linux", "HTML", "CSS", "REST", "API", "Flask", "Django",
            "FastAPI", "Spring", "Laravel", "Symfony", "React Native", "Swift",
            "Kotlin", "Go", "Rust", "TensorFlow", "PyTorch", "Pandas", "NumPy"
        ]
        self.french_cities = [
            "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
            "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes"
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
            print(f"Warning extraction: {e}")
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
            print(f"PDF extraction error: {e}")
            return ""
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extrait le texte d'un document Word"""
        try:
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""
    
    def analyze_cv(self, text: str, filename: str = "") -> dict:
        """Analyse un CV"""
        # Nettoyer le texte
        clean_text = self._clean_text(text)
        
        # Extraire les informations
        personal_info = self._extract_personal_info(clean_text)
        skills = self._extract_skills(clean_text)
        experience = self._extract_experience_info(clean_text)
        education = self._extract_education_info(clean_text)
        
        # Calculer le score de confiance
        confidence = self._calculate_confidence(personal_info, skills, experience)
        
        # Séparer prénom/nom
        full_name = personal_info.get("name", "Candidat")
        first_name, last_name = self._split_name(full_name)
        
        return {
            "success": True,
            "analysis": {
                "confidence_score": confidence,
                "processing_date": datetime.now().isoformat(),
                "char_count": len(text),
                "word_count": len(text.split()),
                "parser_version": "2.0"
            },
            "extracted": {
                "name": full_name,
                "first_name": first_name,
                "last_name": last_name,
                "email": personal_info.get("email", ""),
                "phone": personal_info.get("phone", ""),
                "location": personal_info.get("location", ""),
                "linkedin": personal_info.get("linkedin", ""),
                "skills": skills,
                "experience_years": experience.get("years", 0),
                "experience_details": experience.get("details", ""),
                "education": education.get("details", ""),
                "summary": text[:500] + ("..." if len(text) > 500 else "")
            },
            "metadata": {
                "filename": filename,
                "original_text_preview": text[:1000] if len(text) > 1000 else text
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte"""
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_personal_info(self, text: str) -> dict:
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
            r'\b0[1-9](?:[\s.-]?\d{2}){4}\b',
            r'\b\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\b'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text.replace(' ', ''))
            if matches:
                info["phone"] = matches[0]
                break
        
        # LinkedIn
        linkedin_patterns = [
            r'linkedin\.com/in/[a-zA-Z0-9-]+',
            r'linkedin\.com/company/[a-zA-Z0-9-]+'
        ]
        
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, text)
            if matches:
                info["linkedin"] = f"https://{matches[0]}"
                break
        
        # Localisation
        for city in self.french_cities:
            if city in text:
                info["location"] = city
                break
        
        # Nom (première ligne significative)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:5]:
            if 3 < len(line) < 50:
                if not any(word in line.lower() for word in ['email', 'phone', 'tel', 'cv', 'resume', '@', 'linkedin']):
                    info["name"] = line
                    break
        
        # Si pas de nom trouvé, utiliser "Candidat"
        if not info["name"]:
            info["name"] = "Candidat"
        
        return info
    
    def _split_name(self, full_name: str) -> tuple:
        """Sépare le prénom et le nom"""
        if not full_name or full_name == "Candidat":
            return "", ""
        
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            # Heuristique: prénom = premier mot, nom = autres mots
            return parts[0], " ".join(parts[1:])
    
    def _extract_skills(self, text: str) -> list:
        """Extrait les compétences"""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.skills_list:
            if skill.lower() in text_lower and skill not in found_skills:
                found_skills.append(skill)
        
        return found_skills[:20]
    
    def _extract_experience_info(self, text: str) -> dict:
        """Extrait les informations d'expérience"""
        # Chercher des années d'expérience
        year_patterns = [
            r'(\d+)\s*(ans|années|years|yr)',
            r'expérience\s*:\s*(\d+)',
            r'(\d+)\+?\s*ans?'
        ]
        
        years = 0
        for pattern in year_patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    for match in matches:
                        if isinstance(match, tuple):
                            for item in match:
                                if item.isdigit():
                                    years = int(item)
                                    break
                        elif isinstance(match, str) and match.isdigit():
                            years = int(match)
                    if years > 0:
                        break
                except:
                    pass
        
        # Détecter si c'est un senior/junior
        details = ""
        if "senior" in text.lower() or "expérimenté" in text.lower():
            details = "Expérimenté"
        elif "junior" in text.lower() or "débutant" in text.lower():
            details = "Junior"
        else:
            details = "Intermédiaire"
        
        return {
            "years": years,
            "details": details
        }
    
    def _extract_education_info(self, text: str) -> dict:
        """Extrait les informations de formation"""
        education_keywords = [
            "université", "école", "master", "licence", "bac", "diplôme",
            "formation", "certification", "mba", "doctorat"
        ]
        
        details = ""
        for keyword in education_keywords:
            if keyword in text.lower():
                # Trouver la ligne avec le mot-clé
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if keyword in line.lower():
                        details = line.strip()
                        # Ajouter les lignes suivantes si pertinentes
                        for j in range(i+1, min(i+3, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and len(next_line) > 5:
                                details += f" | {next_line}"
                        break
                if details:
                    break
        
        return {"details": details}
    
    def _calculate_confidence(self, personal_info: dict, skills: list, experience: dict) -> float:
        """Calcule le score de confiance"""
        score = 0.0
        
        if personal_info.get("email"):
            score += 0.3
        if personal_info.get("phone"):
            score += 0.25
        if personal_info.get("name") and personal_info.get("name") != "Candidat":
            score += 0.2
        if skills:
            score += 0.15
        if experience.get("years", 0) > 0:
            score += 0.1
        
        return min(score, 1.0)

# Instance globale
cv_extractor = CVExtractor()

# ========== SUPABASE MANAGER CORRIGÉ ==========
class SupabaseManager:
    """Gestionnaire Supabase corrigé pour votre schéma"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        
        if SUPABASE_AVAILABLE and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabase connected successfully")
            except Exception as e:
                print(f"❌ Supabase connection error: {e}")
                self.client = None
        else:
            self.client = None
            print("⚠️ Supabase not configured")
    
    def save_candidate(self, cv_data: dict, file_hash: str, filename: str, 
                      wp_user_id: int = 0, wp_offer_id: int = 0, message: str = "") -> dict:
        """Sauvegarde un candidat dans votre table Supabase"""
        if not self.client:
            return {"success": False, "error": "Supabase not available"}
        
        try:
            extracted = cv_data.get("extracted", {})
            analysis = cv_data.get("analysis", {})
            
            # Préparer les données EXACTEMENT comme votre table les attend
            candidate_data = {
                # Informations personnelles
                "nom": extracted.get("last_name", "") or extracted.get("name", ""),
                "prenom": extracted.get("first_name", ""),
                "email": extracted.get("email", ""),
                "telephone": extracted.get("phone", ""),
                "adresse": extracted.get("location", ""),
                "linkedin": extracted.get("linkedin", ""),
                
                # Compétences et expérience (format JSON)
                "competences": json.dumps(extracted.get("skills", []), ensure_ascii=False),
                "experiences": json.dumps([{
                    "years": extracted.get("experience_years", 0),
                    "level": extracted.get("experience_details", "")
                }], ensure_ascii=False),
                
                # Formation
                "formations": json.dumps([{
                    "details": extracted.get("education", "")
                }], ensure_ascii=False),
                
                # Langues (à extraire si disponible)
                "langues": json.dumps([], ensure_ascii=False),
                
                # Texte brut
                "raw_text": cv_data.get("metadata", {}).get("original_text_preview", "")[:8000],
                
                # Métiers (basé sur les compétences)
                "metiers": ", ".join(extracted.get("skills", []))[:200],
                
                # Entreprise et postes
                "entreprise": "",
                "postes": extracted.get("experience_details", ""),
                
                # Profil
                "profil": extracted.get("summary", ""),
                
                # Fichier
                "fichier": filename,
                "cv_filename": filename,
                "file_hash": file_hash,
                "file_type": filename.split('.')[-1] if '.' in filename else "",
                
                # URLs
                "lien": "",
                "cv_url": "",
                
                # Niveau
                "niveau": "mid-level",  # À déterminer plus finement
                
                # Expérience
                "annees_experience": float(extracted.get("experience_years", 0)),
                
                # Statuts
                "status": "analysé",
                "statut": "analysé",
                "parse_status": "success",
                
                # Dates
                "date_import": datetime.now().isoformat(),
                "date_analyse": datetime.now().isoformat(),
                "date_extraction": datetime.now().isoformat(),
                "extraction_date": datetime.now().isoformat(),
                
                # Source
                "source": "python_api",
                
                # Score de confiance
                "confidence_score": float(analysis.get("confidence_score", 0.0)),
                
                # WordPress info
                "wp_user_id": wp_user_id,
                "user_id": wp_user_id,
                "user_name": "",
                "wp_offer_id": wp_offer_id,
                "offre_id": wp_offer_id,
                "offre_postulee": wp_offer_id if wp_offer_id else None,
                
                # Message de candidature
                "message_candidature": message
            }
            
            # Nettoyer les valeurs None (Supabase les rejette)
            for key, value in list(candidate_data.items()):
                if value is None:
                    candidate_data[key] = ""
            
            print(f"📤 Inserting into Supabase: {filename}")
            print(f"   Email: {candidate_data.get('email')}")
            print(f"   Name: {candidate_data.get('nom')} {candidate_data.get('prenom')}")
            print(f"   Skills: {len(extracted.get('skills', []))}")
            
            # Insérer dans Supabase
            response = self.client.table("candidats").insert(candidate_data).execute()
            
            if response.data:
                candidate_id = response.data[0].get("id")
                print(f"✅ Inserted successfully, ID: {candidate_id}")
                return {
                    "success": True,
                    "candidate_id": candidate_id,
                    "action": "created"
                }
            else:
                error_msg = "No data returned from Supabase"
                print(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            print(f"❌ Supabase save error: {e}")
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
        "supabase": "connected" if supabase_manager.client else "disconnected"
    }

@app.get("/health")
async def health():
    return {
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "operational",
            "extractor": "ready",
            "supabase": "connected" if supabase_manager.client else "disconnected"
        }
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
        
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(400, "File too large (max 10MB)")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        
        if not text or len(text.strip()) < 20:
            return JSONResponse({
                "success": True,
                "warning": "Insufficient text for analysis",
                "extracted": {"filename": file.filename}
            })
        
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
                filename=file.filename
            )
            
            if save_result["success"]:
                result["supabase"] = save_result
            else:
                result["supabase"] = {"success": False, "error": save_result.get("error")}
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/process-wordpress-upload")
async def process_wordpress_upload(
    file: UploadFile = File(...),
    wp_user_id: int = Form(0),
    wp_offer_id: int = Form(0),
    message: str = Form("")
):
    """Endpoint spécial pour WordPress - CORRIGÉ"""
    try:
        print(f"📥 WordPress upload received:")
        print(f"   Filename: {file.filename}")
        print(f"   User ID: {wp_user_id}")
        print(f"   Offer ID: {wp_offer_id}")
        
        if not file.filename:
            raise HTTPException(400, "Filename required")
        
        file_content = await file.read()
        print(f"   File size: {len(file_content)} bytes")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        print(f"   Extracted text length: {len(text)} chars")
        
        if not text or len(text.strip()) < 20:
            print("⚠️ Insufficient text")
            return {
                "success": True,
                "warning": "Insufficient text",
                "extracted": {
                    "name": "Candidat",
                    "email": "",
                    "phone": "",
                    "skills": []
                }
            }
        
        # Analyser le CV
        result = cv_extractor.analyze_cv(text, file.filename)
        extracted = result.get("extracted", {})
        print(f"   Analysis results:")
        print(f"     Name: {extracted.get('name')}")
        print(f"     Email: {extracted.get('email')}")
        print(f"     Phone: {extracted.get('phone')}")
        print(f"     Skills: {len(extracted.get('skills', []))}")
        
        # Calculer le hash
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase avec infos WordPress
        save_result = {}
        if supabase_manager.client:
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename,
                wp_user_id=wp_user_id,
                wp_offer_id=wp_offer_id,
                message=message
            )
            print(f"   Supabase save result: {save_result.get('success')}")
        
        response = {
            "success": True,
            "message": "CV analysé avec succès",
            "analysis": result.get("analysis", {}),
            "extracted": extracted,
            "supabase": save_result,
            "file_info": {
                "original_name": file.filename,
                "file_hash": file_hash,
                "size": len(file_content)
            }
        }
        
        if message:
            response["candidate_message"] = message
        
        print("✅ Request processed successfully")
        return response
        
    except Exception as e:
        print(f"❌ WordPress upload error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/test-supabase")
async def test_supabase():
    """Test Supabase"""
    if not supabase_manager.client:
        return {"connected": False, "error": "Client not initialized"}
    
    try:
        # Test simple de connexion
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
    print(f"🚀 TruthTalent API started on port {port}")
    print(f"📦 PDF support: {PDF_AVAILABLE}")
    print(f"📄 DOCX support: {DOCX_AVAILABLE}")
    print(f"📊 Supabase: {SUPABASE_AVAILABLE and bool(SUPABASE_KEY)}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1
    )