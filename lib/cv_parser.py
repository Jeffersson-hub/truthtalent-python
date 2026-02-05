# lib/cv_parser.py - VERSION CORRIGÉE
import os
import json
import re
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
from io import BytesIO
import traceback

class CVParser:
    """Parser de CV simplifié"""
    
    def parse_cv(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Parser un fichier CV et extraire les informations"""
        try:
            print(f"🔍 Début parsing CV: {filename}")
            
            # Extraction du texte selon le format
            text = self.extract_text(file_content, filename)
            
            if not text or len(text.strip()) < 10:
                return self.get_fallback_data()
            
            # Extraction des informations
            result = {
                "success": True,
                "raw_text": text[:2000],  # Limiter la taille
                "nom": self.extract_name(text),
                "prenom": "",
                "email": self.extract_email(text),
                "telephone": self.extract_phone(text),
                "competences": self.extract_skills(text),
                "niveau": self.extract_level(text),
                "annees_experience": self.extract_experience(text),
                "confidence_score": 0.7,
                "parse_status": "success"
            }
            
            print(f"✅ Parsing réussi pour {filename}")
            return result
            
        except Exception as e:
            print(f"❌ Erreur parsing: {e}")
            traceback.print_exc()
            return self.get_fallback_data()
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extraire le texte selon le format du fichier"""
        try:
            filename_lower = filename.lower()
            
            if filename_lower.endswith('.pdf'):
                return self.extract_from_pdf(file_content)
            elif filename_lower.endswith(('.doc', '.docx')):
                return self.extract_from_doc(file_content)
            elif filename_lower.endswith(('.txt', '.rtf')):
                return file_content.decode('utf-8', errors='ignore')
            else:
                # Pour les images ou autres formats, retourner un texte minimal
                return f"Fichier: {filename}"
                
        except Exception as e:
            print(f"⚠️ Erreur extraction texte: {e}")
            return ""
    
    def extract_from_pdf(self, file_content: bytes) -> str:
        """Extraire le texte d'un PDF"""
        try:
            import pdfplumber
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n".join(text_parts)
        except ImportError:
            return "PDF (pdfplumber non disponible)"
        except Exception as e:
            return f"PDF (erreur: {str(e)[:50]})"
    
    def extract_from_doc(self, file_content: bytes) -> str:
        """Extraire le texte d'un document Word"""
        try:
            from docx import Document
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except ImportError:
            return "DOC (python-docx non disponible)"
        except Exception:
            return "DOC (erreur d'extraction)"
    
    def extract_email(self, text: str) -> str:
        """Extraire l'email du texte"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else ""
    
    def extract_phone(self, text: str) -> str:
        """Extraire le numéro de téléphone"""
        phone_patterns = [
            r'\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            r'\b\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}[-.\s]?\d{2}\b'
        ]
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return ""
    
    def extract_name(self, text: str) -> str:
        """Tenter d'extraire le nom"""
        lines = text.split('\n')
        for line in lines[:5]:  # Chercher dans les premières lignes
            line = line.strip()
            if line and len(line) > 2 and not any(word in line.lower() for word in ['email', 'phone', 'tel', 'cv', 'resume']):
                return line[:50]
        return "Candidat"
    
    def extract_skills(self, text: str) -> List[str]:
        """Extraire les compétences"""
        skills_list = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'PHP', 'Ruby',
            'HTML', 'CSS', 'React', 'Vue', 'Angular', 'Node.js', 'Django',
            'Flask', 'FastAPI', 'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL',
            'MySQL', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Git',
            'Linux', 'Windows', 'MacOS', 'REST', 'API', 'GraphQL', 'JSON',
            'XML', 'TypeScript', 'Go', 'Rust', 'Swift', 'Kotlin'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skills_list:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills[:15]  # Limiter à 15 compétences
    
    def extract_level(self, text: str) -> str:
        """Déterminer le niveau d'expérience"""
        text_lower = text.lower()
        
        keywords = {
            "senior": ["senior", "lead", "principal", "architect", "expert"],
            "mid-level": ["mid-level", "intermediate", "confirmed"],
            "junior": ["junior", "entry", "débutant", "graduate"],
            "intern": ["intern", "stagiaire", "apprentice"]
        }
        
        for level, words in keywords.items():
            for word in words:
                if word in text_lower:
                    return level
        
        return "mid-level"  # Par défaut
    
    def extract_experience(self, text: str) -> float:
        """Estimer les années d'expérience"""
        # Chercher des motifs comme "5 ans", "3 years", etc.
        patterns = [
            r'(\d+)\s*(ans|années|years|yr)',
            r'(\d+)\+?\s*ans?',
            r'expérience\s*:\s*(\d+)',
            r'experience\s*:\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    # Prendre la première valeur numérique trouvée
                    for match in matches:
                        if isinstance(match, tuple):
                            for item in match:
                                if item.isdigit():
                                    return float(item)
                        elif isinstance(match, str) and match.isdigit():
                            return float(match)
                except:
                    pass
        
        # Estimation basée sur les mots-clés
        text_lower = text.lower()
        if any(word in text_lower for word in ['senior', 'lead', 'principal']):
            return 7.0
        elif any(word in text_lower for word in ['mid', 'intermediate', 'confirmed']):
            return 3.0
        elif any(word in text_lower for word in ['junior', 'entry', 'graduate']):
            return 1.0
        else:
            return 2.0  # Valeur par défaut
    
    def get_fallback_data(self) -> Dict[str, Any]:
        """Données de secours en cas d'erreur"""
        return {
            "success": True,
            "raw_text": "",
            "nom": "Candidat",
            "prenom": "",
            "email": "",
            "telephone": "",
            "competences": [],
            "niveau": "mid-level",
            "annees_experience": 2.0,
            "confidence_score": 0.3,
            "parse_status": "fallback"
        }