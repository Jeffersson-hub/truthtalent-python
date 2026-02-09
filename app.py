#!/usr/bin/env python3
"""
TruthTalent API - Extracteur AVANCÉ de CV
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
    description="API d'extraction avancée de CV",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== CV EXTRACTOR AVANCÉ ==========
class AdvancedCVExtractor:
    """Extracteur de CV avancé avec parsing intelligent"""
    
    def __init__(self):
        self.skills_list = self._load_skills_database()
        self.french_cities = [
            "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
            "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes",
            "Toulon", "Grenoble", "Dijon", "Angers", "Le Havre"
        ]
        self.languages = [
            "français", "anglais", "espagnol", "allemand", "italien", 
            "portugais", "néerlandais", "chinois", "japonais", "arabe",
            "russe", "hindi", "coréen"
        ]
        self.degree_keywords = {
            "bac": "Baccalauréat",
            "bts": "BTS",
            "dut": "DUT",
            "licence": "Licence",
            "master": "Master",
            "mba": "MBA",
            "doctorat": "Doctorat",
            "phd": "PhD",
            "ingénieur": "Diplôme d'ingénieur"
        }
    
    def _load_skills_database(self):
        """Base de données complète de compétences"""
        return {
            "backend": ["Python", "Java", "C#", "PHP", "Ruby", "Node.js", "Go", "Rust", "Scala", "Kotlin"],
            "frontend": ["JavaScript", "TypeScript", "React", "Vue.js", "Angular", "Svelte", "Next.js", "Nuxt.js"],
            "devops": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Jenkins", "GitLab CI", "Ansible"],
            "mobile": ["Swift", "Kotlin", "Flutter", "React Native", "Ionic", "Xamarin"],
            "database": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Oracle", "SQL Server"],
            "data": ["Python", "R", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Tableau", "Power BI", "Spark"],
            "design": ["Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator", "InDesign", "Premiere Pro"],
            "management": ["Jira", "Confluence", "Trello", "Asana", "Notion", "Slack", "Teams"],
            "cloud": ["AWS", "Azure", "GCP", "Heroku", "DigitalOcean", "OVH"],
            "testing": ["Jest", "Mocha", "Cypress", "Selenium", "JUnit", "TestNG"]
        }
    
    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extrait le texte du fichier"""
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
            print(f"⚠️ Erreur extraction texte: {e}")
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
            print(f"❌ PDF extraction error: {e}")
            return ""
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extrait le texte d'un document Word"""
        try:
            doc = Document(BytesIO(file_content))
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            print(f"❌ DOCX extraction error: {e}")
            return ""
    
    def analyze_cv(self, text: str, filename: str = "") -> dict:
        """Analyse complète d'un CV"""
        print(f"🔍 Analyse du CV: {filename}")
        
        # Nettoyer et normaliser le texte
        clean_text = self._clean_text(text)
        print(f"   Texte nettoyé: {len(clean_text)} caractères")
        
        # Extraire toutes les informations
        personal_info = self._extract_personal_info(clean_text)
        print(f"   Infos perso: {personal_info.get('name')}, {personal_info.get('email')}")
        
        skills = self._extract_skills_comprehensive(clean_text)
        print(f"   Compétences trouvées: {len(skills)}")
        
        experience = self._extract_experience_details(clean_text)
        print(f"   Expérience: {experience.get('years', 0)} ans, {experience.get('level')}")
        
        education = self._extract_education_details(clean_text)
        print(f"   Éducation: {education.get('degree')}")
        
        languages = self._extract_languages_details(clean_text)
        print(f"   Langues: {len(languages)}")
        
        # Calculer le score de confiance
        confidence = self._calculate_confidence(personal_info, skills, experience)
        print(f"   Score confiance: {confidence}")
        
        # Séparer prénom/nom
        full_name = personal_info.get("name", "Candidat")
        first_name, last_name = self._split_name(full_name)
        
        # Préparer les métiers (basé sur les compétences principales)
        metiers = self._extract_metiers(skills)
        
        return {
            "success": True,
            "analysis": {
                "confidence_score": confidence,
                "processing_date": datetime.now().isoformat(),
                "char_count": len(text),
                "word_count": len(text.split()),
                "parser_version": "3.0"
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
                "skills_by_category": self._categorize_skills(skills),
                "languages": languages,
                "experience_years": experience.get("years", 0),
                "experience_level": experience.get("level", ""),
                "experience_details": experience.get("positions", []),
                "education_degree": education.get("degree", ""),
                "education_institution": education.get("institution", ""),
                "education_details": education.get("details", []),
                "summary": self._extract_summary(clean_text),
                "metiers": metiers
            },
            "metadata": {
                "filename": filename,
                "original_text_preview": text[:1000] if len(text) > 1000 else text,
                "has_email": bool(personal_info.get("email")),
                "has_phone": bool(personal_info.get("phone")),
                "has_name": bool(personal_info.get("name")),
                "has_skills": bool(skills),
                "has_experience": bool(experience.get("years", 0) > 0)
            }
        }
    
    def _clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte"""
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        # Normaliser les retours à la ligne
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def _extract_personal_info(self, text: str) -> dict:
        """Extrait les informations personnelles de manière robuste"""
        info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": ""
        }
        
        # 1. EMAIL - Recherche approfondie
        email_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'[Ee]-?[Mm][Aa][Ii][Ll]\s*[:]\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            r'[Cc]ontact\s*[:]\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})'
        ]
        
        for pattern in email_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    info["email"] = matches[0][0]
                else:
                    info["email"] = matches[0]
                break
        
        # 2. TÉLÉPHONE - Formats français/internationaux
        phone_patterns = [
            r'(?:(?:\+|00)33\s?|0)[1-9](?:[\s.-]?\d{2}){4}',
            r'\b0[1-9](?:[\s.-]?\d{2}){4}\b',
            r'\b\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2}\b',
            r'T[ée]l[\.]?\s*[:]?\s*(\+?\d[\d\s.-]{8,}\d)',
            r'[Pp]hone\s*[:]?\s*(\+?\d[\d\s.-]{8,}\d)'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                phone = matches[0] if isinstance(matches[0], str) else matches[0][0]
                # Nettoyer le numéro
                phone = re.sub(r'[^\d+]', '', phone)
                if len(phone) >= 10:
                    info["phone"] = phone
                    break
        
        # 3. LINKEDIN
        linkedin_patterns = [
            r'(?:linkedin\.com/(?:in|company)/[a-zA-Z0-9-]+)',
            r'[Ll]inked[Ii]n\s*[:]\s*(?:linkedin\.com/(?:in|company)/[a-zA-Z0-9-]+)',
            r'[Pp]rofil\s+[Ll]inked[Ii]n\s*[:].*?(linkedin\.com/(?:in|company)/[a-zA-Z0-9-]+)'
        ]
        
        for pattern in linkedin_patterns:
            matches = re.findall(pattern, text)
            if matches:
                linkedin = matches[0]
                if not linkedin.startswith('http'):
                    linkedin = f"https://{linkedin}"
                info["linkedin"] = linkedin
                break
        
        # 4. LOCALISATION
        for city in self.french_cities:
            if re.search(r'\b' + re.escape(city) + r'\b', text, re.IGNORECASE):
                info["location"] = city
                break
        
        # 5. NOM - Algorithmie avancée
        lines = text.split('\n')
        
        # Stratégie 1: Chercher un nom en début de document (haut du CV)
        for i in range(min(10, len(lines))):
            line = lines[i].strip()
            if 2 <= len(line.split()) <= 4 and len(line) > 3 and len(line) < 50:
                # Vérifier que ce n'est pas un en-tête ou une section
                if not any(word in line.lower() for word in [
                    'cv', 'curriculum', 'vitae', 'resume', 'profil',
                    'experience', 'expérience', 'formation', 'education',
                    'compétences', 'skills', 'contact', 'coordonnées'
                ]):
                    # Vérifier qu'il n'y a pas d'email ou téléphone
                    if not re.search(r'@|\d{10}', line):
                        info["name"] = line
                        break
        
        # Stratégie 2: Chercher autour des mots-clés "Nom", "Prénom"
        if not info["name"]:
            name_patterns = [
                r'[Nn]om\s*[:]\s*([^\n]{2,30})',
                r'[Pp]r[ée]nom\s*[:]\s*([^\n]{2,20})',
                r'[Ff]ull\s+[Nn]ame\s*[:]\s*([^\n]{2,30})'
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    info["name"] = matches[0].strip()
                    break
        
        # Stratégie 3: Première ligne significative sans caractères spéciaux
        if not info["name"]:
            for line in lines[:5]:
                line = line.strip()
                if (3 <= len(line) <= 40 and 
                    not re.search(r'[@\d{10}]', line) and
                    not any(word in line.lower() for word in ['email', 'phone', 'tel', 'cv', 'resume'])):
                    info["name"] = line
                    break
        
        if not info["name"]:
            info["name"] = "Candidat"
        
        return info
    
    def _split_name(self, full_name: str) -> tuple:
        """Sépare intelligemment le prénom et le nom"""
        if not full_name or full_name == "Candidat":
            return "", ""
        
        # Nettoyer le nom
        name = full_name.strip()
        
        # Retirer les titres
        titles = ['M.', 'Mme', 'Mr', 'Mrs', 'Ms', 'Dr', 'Prof']
        for title in titles:
            if name.startswith(title):
                name = name[len(title):].strip()
        
        parts = name.split()
        
        if len(parts) == 1:
            return parts[0], ""
        elif len(parts) == 2:
            return parts[0], parts[1]
        else:
            # Heuristique: prénom = premier mot, nom = derniers mots
            first_name = parts[0]
            last_name = " ".join(parts[1:])
            return first_name, last_name
    
    def _extract_skills_comprehensive(self, text: str) -> list:
        """Extrait les compétences de manière exhaustive"""
        found_skills = []
        text_lower = text.lower()
        
        # Rechercher toutes les compétences par catégorie
        for category, skills in self.skills_list.items():
            for skill in skills:
                # Recherche insensible à la casse
                if skill.lower() in text_lower:
                    # Vérifier que ce n'est pas un faux positif
                    skill_pattern = r'\b' + re.escape(skill) + r'\b'
                    if re.search(skill_pattern, text, re.IGNORECASE):
                        if skill not in found_skills:
                            found_skills.append(skill)
        
        # Rechercher des compétences par motifs
        skill_patterns = [
            r'(?:compétences|skills)\s*[:]([^:]{10,500})',
            r'(?:expertise|expertises)\s*[:]([^:]{10,500})',
            r'(?:technologies|technologies?)\s*[:]([^:]{10,500})'
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                skills_text = matches[0].lower()
                # Chercher des mots-clés techniques
                tech_keywords = ['python', 'java', 'javascript', 'react', 'docker', 'aws']
                for keyword in tech_keywords:
                    if keyword in skills_text:
                        skill_name = keyword.capitalize()
                        if skill_name not in found_skills:
                            found_skills.append(skill_name)
        
        return found_skills[:25]  # Limiter à 25 compétences
    
    def _categorize_skills(self, skills: list) -> dict:
        """Catégorise les compétences"""
        categorized = {}
        for category, category_skills in self.skills_list.items():
            category_found = []
            for skill in skills:
                if skill in category_skills:
                    category_found.append(skill)
            if category_found:
                categorized[category] = category_found
        return categorized
    
    def _extract_languages_details(self, text: str) -> list:
        """Extrait les langues avec leur niveau"""
        languages_found = []
        text_lower = text.lower()
        
        # Chercher une section langues
        lang_section_patterns = [
            r'[Ll]angues?\s*[:]([^:]{10,300})',
            r'[Ll]anguages?\s*[:]([^:]{10,300})'
        ]
        
        lang_section = ""
        for pattern in lang_section_patterns:
            matches = re.findall(pattern, text)
            if matches:
                lang_section = matches[0]
                break
        
        # Si pas de section, chercher dans tout le texte
        if not lang_section:
            lang_section = text_lower
        
        # Niveaux de langue
        levels = {
            'débutant': 'Débutant',
            'intermédiaire': 'Intermédiaire',
            'avancé': 'Avancé',
            'courant': 'Courant',
            'natif': 'Natif',
            'bilingue': 'Bilingue',
            'beginner': 'Débutant',
            'intermediate': 'Intermédiaire',
            'advanced': 'Avancé',
            'fluent': 'Courant',
            'native': 'Natif',
            'bilingual': 'Bilingue'
        }
        
        for lang in self.languages:
            lang_pattern = r'\b' + re.escape(lang) + r'\b'
            if re.search(lang_pattern, lang_section, re.IGNORECASE):
                # Chercher le niveau associé
                lang_with_level = lang.capitalize()
                
                # Chercher le niveau dans les 10 mots autour de la langue
                words = lang_section.split()
                for i, word in enumerate(words):
                    if lang in word:
                        # Chercher niveau avant ou après
                        for j in range(max(0, i-3), min(len(words), i+4)):
                            if words[j] in levels:
                                lang_with_level += f" ({levels[words[j]]})"
                                break
                
                if lang_with_level not in languages_found:
                    languages_found.append(lang_with_level)
        
        return languages_found
    
    def _extract_experience_details(self, text: str) -> dict:
        """Extrait les détails d'expérience"""
        result = {
            "years": 0,
            "level": "",
            "positions": []
        }
        
        # 1. Extraire les années d'expérience
        year_patterns = [
            r'(\d+)\s*(?:ans|années|years|yr)s?\s*(?:d\'?expérience|experience)',
            r'expérience\s*(?:professionnelle)?\s*[:=]\s*(\d+)\s*(?:ans|années|years)',
            r'(\d+)\+?\s*(?:ans|années)',
            r'(\d+)\s*ans?\s*d\'?exp'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    years = int(matches[0])
                    result["years"] = years
                    break
                except:
                    pass
        
        # 2. Déterminer le niveau
        level_keywords = {
            "senior": ["senior", "lead", "principal", "architect", "expert", "chef", "manager", "directeur"],
            "mid-level": ["mid-level", "intermediate", "confirmed", "expérimenté", "confirmé"],
            "junior": ["junior", "entry", "débutant", "graduate", "jeune diplômé"],
            "intern": ["intern", "stagiaire", "apprenti", "alternance", "apprentissage"]
        }
        
        text_lower = text.lower()
        for level, keywords in level_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    result["level"] = level
                    break
            if result["level"]:
                break
        
        # Si pas de niveau détecté, estimer d'après l'expérience
        if not result["level"]:
            if result["years"] >= 7:
                result["level"] = "senior"
            elif result["years"] >= 3:
                result["level"] = "mid-level"
            elif result["years"] > 0:
                result["level"] = "junior"
            else:
                result["level"] = "intern"
        
        # 3. Extraire les postes
        position_patterns = [
            r'\b(?:20\d{2}|19\d{2})\s*[-–]\s*(?:présent|actuel|20\d{2}|19\d{2})',
            r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\s*[-–]',
            r'\b(?:janv|fév|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)[a-z]*\s+\d{4}\s*[-–]'
        ]
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for pattern in position_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    position_info = {
                        "period": re.search(pattern, line, re.IGNORECASE).group(),
                        "title": self._extract_job_title(line),
                        "company": self._extract_company(line)
                    }
                    result["positions"].append(position_info)
                    break
        
        return result
    
    def _extract_job_title(self, line: str) -> str:
        """Extrait le titre du poste"""
        # Retirer les dates
        line = re.sub(r'\b(?:20\d{2}|19\d{2})\s*[-–].*', '', line)
        line = re.sub(r'\b(?:jan|feb|mar)[a-z]*\s+\d{4}\s*[-–].*', '', line, flags=re.IGNORECASE)
        
        # Retirer les indicateurs
        indicators = ["chez", "at", "|", "-", "•", "·", ":", ";"]
        for indicator in indicators:
            if indicator in line:
                parts = line.split(indicator)
                line = parts[0].strip()
                break
        
        return line.strip()[:100]
    
    def _extract_company(self, line: str) -> str:
        """Extrait le nom de l'entreprise"""
        indicators = ["chez", "at", "|", "-", "•", "·", ":", ";"]
        for indicator in indicators:
            if indicator in line:
                parts = line.split(indicator)
                if len(parts) > 1:
                    return parts[1].strip()[:100]
        return ""
    
    def _extract_education_details(self, text: str) -> dict:
        """Extrait les détails de formation"""
        result = {
            "degree": "",
            "institution": "",
            "details": []
        }
        
        # Chercher une section éducation
        edu_patterns = [
            r'[ÉEe]ducation\s*[:]([^:]{10,500})',
            r'[Ff]ormation\s*[:]([^:]{10,500})',
            r'[Pp]arcours\s+[Aa]cad[ée]mique\s*[:]([^:]{10,500})'
        ]
        
        edu_section = ""
        for pattern in edu_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                edu_section = matches[0]
                break
        
        # Si pas de section, chercher dans tout le texte
        if not edu_section:
            edu_section = text
        
        # Chercher les diplômes
        for keyword, degree in self.degree_keywords.items():
            if re.search(r'\b' + re.escape(keyword) + r'\b', edu_section, re.IGNORECASE):
                result["degree"] = degree
                break
        
        # Chercher les établissements
        institutions = ["université", "école", "institut", "faculté", "polytechnique"]
        lines = edu_section.split('\n')
        for line in lines:
            for inst in institutions:
                if inst in line.lower():
                    result["institution"] = line.strip()
                    break
            if result["institution"]:
                break
        
        # Collecter les détails
        lines = edu_section.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and not any(word in line.lower() for word in ['education', 'formation']):
                result["details"].append(line)
        
        return result
    
    def _extract_metiers(self, skills: list) -> str:
        """Extrait les métiers basés sur les compétences"""
        metier_mapping = {
            "développeur": ["Python", "Java", "JavaScript", "C#", "PHP"],
            "devops": ["Docker", "Kubernetes", "AWS", "Terraform", "Jenkins"],
            "data scientist": ["Python", "TensorFlow", "PyTorch", "Pandas", "R"],
            "designer": ["Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator"],
            "administrateur": ["SQL", "PostgreSQL", "MySQL", "Linux", "Windows"]
        }
        
        metiers = []
        for metier, required_skills in metier_mapping.items():
            matches = sum(1 for skill in skills if skill in required_skills)
            if matches >= 2:  # Au moins 2 compétences correspondantes
                metiers.append(metier)
        
        return ", ".join(metiers) if metiers else "Développeur"
    
    def _extract_summary(self, text: str) -> str:
        """Extrait un résumé du CV"""
        # Chercher une section profil/résumé
        summary_patterns = [
            r'[Pp]rofil\s*[:]([^:]{20,300})',
            r'[Ss]ummary\s*[:]([^:]{20,300})',
            r'[ÀAàa]\s+[Pp]ropos\s*[:]([^:]{20,300})',
            r'[Oo]bjectif\s*[:]([^:]{20,300})'
        ]
        
        for pattern in summary_patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()[:500]
        
        # Sinon, prendre les premières phrases significatives
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if 10 <= len(sentence.split()) <= 30:
                keywords = ["expérience", "compétences", "spécialisé", "passionné", "expert"]
                if any(keyword in sentence.lower() for keyword in keywords):
                    return sentence[:300]
        
        # Fallback
        return text[:200] + ("..." if len(text) > 200 else "")
    
    def _calculate_confidence(self, personal_info: dict, skills: list, experience: dict) -> float:
        """Calcule le score de confiance"""
        score = 0.0
        
        # Points pour informations personnelles
        if personal_info.get("email"):
            score += 0.3
        if personal_info.get("phone"):
            score += 0.25
        if personal_info.get("name") and personal_info["name"] != "Candidat":
            score += 0.2
        if personal_info.get("location"):
            score += 0.05
        
        # Points pour compétences
        if skills:
            score += min(0.2, len(skills) * 0.01)
        
        # Points pour expérience
        if experience.get("years", 0) > 0:
            score += 0.1
        if experience.get("positions"):
            score += 0.05
        
        return min(score, 1.0)

# Instance globale
cv_extractor = AdvancedCVExtractor()

# ========== SUPABASE MANAGER AMÉLIORÉ ==========
class SupabaseManager:
    """Gestionnaire Supabase amélioré"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        
        if SUPABASE_AVAILABLE and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                print("✅ Supabase connecté avec succès")
            except Exception as e:
                print(f"❌ Erreur connexion Supabase: {e}")
                self.client = None
        else:
            self.client = None
            print("⚠️ Supabase non configuré")
    
    def save_candidate(self, cv_data: dict, file_hash: str, filename: str, 
                      wp_user_id: int = 0, wp_offer_id: int = 0, message: str = "") -> dict:
        """Sauvegarde un candidat avec toutes les données extraites"""
        if not self.client:
            return {"success": False, "error": "Supabase non disponible"}
        
        try:
            extracted = cv_data.get("extracted", {})
            analysis = cv_data.get("analysis", {})
            metadata = cv_data.get("metadata", {})
            
            print(f"📤 Préparation données Supabase pour: {filename}")
            print(f"   Nom: {extracted.get('name')}")
            print(f"   Email: {extracted.get('email')}")
            print(f"   Téléphone: {extracted.get('phone')}")
            print(f"   Compétences: {len(extracted.get('skills', []))}")
            print(f"   Langues: {len(extracted.get('languages', []))}")
            print(f"   Expérience: {extracted.get('experience_years', 0)} ans")
            
            # Préparer les données EXACTEMENT pour votre table
            candidate_data = {
                # Informations personnelles
                "nom": extracted.get("last_name", ""),
                "prenom": extracted.get("first_name", ""),
                "email": extracted.get("email", ""),
                "telephone": extracted.get("phone", ""),
                "adresse": extracted.get("location", ""),
                "linkedin": extracted.get("linkedin", ""),
                
                # Compétences (JSON)
                "competences": json.dumps(extracted.get("skills", []), ensure_ascii=False),
                
                # Expériences (JSON structuré)
                "experiences": json.dumps({
                    "total_years": extracted.get("experience_years", 0),
                    "level": extracted.get("experience_level", ""),
                    "positions": extracted.get("experience_details", [])
                }, ensure_ascii=False),
                
                # Formations (JSON structuré)
                "formations": json.dumps({
                    "degree": extracted.get("education_degree", ""),
                    "institution": extracted.get("education_institution", ""),
                    "details": extracted.get("education_details", [])
                }, ensure_ascii=False),
                
                # Langues (JSON)
                "langues": json.dumps(extracted.get("languages", []), ensure_ascii=False),
                
                # Texte brut
                "raw_text": metadata.get("original_text_preview", "")[:8000],
                
                # Métiers (basé sur les compétences)
                "metiers": extracted.get("metiers", "Développeur"),
                
                # Entreprise (à déterminer)
                "entreprise": "",
                
                # Postes (expérience récente)
                "postes": extracted.get("experience_level", "Développeur"),
                
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
                "niveau": extracted.get("experience_level", "mid-level"),
                
                # Années d'expérience
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
                "source": "wordpress_plugin",
                
                # Score de confiance
                "confidence_score": float(analysis.get("confidence_score", 0.0)),
                
                # WordPress info
                "wp_user_id": wp_user_id if wp_user_id else None,
                "user_id": wp_user_id if wp_user_id else None,
                "user_name": "",
                "wp_offer_id": wp_offer_id if wp_offer_id else None,
                "offre_id": wp_offer_id if wp_offer_id else None,
                "offre_postulee": wp_offer_id if wp_offer_id else None,
                
                # Message de candidature
                "message_candidature": message
            }
            
            # Nettoyer les valeurs None pour Supabase
            for key, value in list(candidate_data.items()):
                if value is None:
                    candidate_data[key] = ""
                elif isinstance(value, (int, float)) and value == 0:
                    candidate_data[key] = 0
                elif isinstance(value, str) and value == "":
                    candidate_data[key] = ""
            
            print(f"📊 Données à insérer dans Supabase:")
            print(f"   JSON competences: {candidate_data.get('competences', '')[:100]}...")
            print(f"   JSON experiences: {candidate_data.get('experiences', '')[:100]}...")
            print(f"   JSON formations: {candidate_data.get('formations', '')[:100]}...")
            print(f"   JSON langues: {candidate_data.get('langues', '')[:100]}...")
            
            # Insérer dans Supabase
            response = self.client.table("candidats").insert(candidate_data).execute()
            
            if response.data:
                candidate_id = response.data[0].get("id")
                print(f"✅ Candidat inséré avec succès, ID: {candidate_id}")
                
                # Vérifier l'insertion
                check = self.client.table("candidats").select("*").eq("id", candidate_id).execute()
                if check.data:
                    inserted_data = check.data[0]
                    print(f"📋 Données vérifiées dans Supabase:")
                    print(f"   Nom: {inserted_data.get('nom')} {inserted_data.get('prenom')}")
                    print(f"   Email: {inserted_data.get('email')}")
                    print(f"   Téléphone: {inserted_data.get('telephone')}")
                    print(f"   Compétences: {inserted_data.get('competences', '')[:50]}...")
                    print(f"   Langues: {inserted_data.get('langues', '')[:50]}...")
                
                return {
                    "success": True,
                    "candidate_id": candidate_id,
                    "action": "created"
                }
            else:
                error_msg = "Aucune donnée retournée par Supabase"
                print(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            print(f"❌ Erreur sauvegarde Supabase: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

# Instance globale
supabase_manager = SupabaseManager()

# ========== ROUTES API ==========
@app.get("/")
async def root():
    return {
        "service": "TruthTalent CV Parser Advanced",
        "version": "3.0.0",
        "status": "online",
        "features": ["extraction_avancée", "supabase_integration", "wordpress_compatible"]
    }

@app.get("/health")
async def health():
    return {
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "extractor": "ready",
        "supabase": "connected" if supabase_manager.client else "disconnected"
    }

@app.post("/extract")
async def extract_cv(file: UploadFile = File(...)):
    """Analyse avancée d'un CV"""
    try:
        print(f"📥 Requête d'extraction reçue: {file.filename}")
        
        if not file.filename:
            raise HTTPException(400, "Nom de fichier requis")
        
        file_content = await file.read()
        print(f"   Taille fichier: {len(file_content)} bytes")
        
        if len(file_content) == 0:
            raise HTTPException(400, "Fichier vide")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        print(f"   Texte extrait: {len(text)} caractères")
        
        if not text or len(text.strip()) < 50:
            print("⚠️ Texte insuffisant pour analyse")
            return JSONResponse({
                "success": True,
                "warning": "Texte insuffisant pour analyse approfondie",
                "extracted": {"filename": file.filename}
            })
        
        # Analyser le CV
        print("🔍 Début de l'analyse du CV...")
        result = cv_extractor.analyze_cv(text, file.filename)
        print("✅ Analyse terminée")
        
        # Calculer le hash
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase
        save_result = {}
        if supabase_manager.client:
            print("💾 Sauvegarde dans Supabase...")
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename
            )
            
            if save_result["success"]:
                result["supabase"] = save_result
                print("✅ Sauvegarde Supabase réussie")
            else:
                result["supabase"] = {"success": False, "error": save_result.get("error")}
                print(f"⚠️ Erreur sauvegarde Supabase: {save_result.get('error')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": f"Erreur interne: {str(e)}"},
            status_code=500
        )

@app.post("/process-wordpress-upload")
async def process_wordpress_upload(
    file: UploadFile = File(...),
    wp_user_id: int = Form(0),
    wp_offer_id: int = Form(0),
    message: str = Form("")
):
    """Endpoint pour WordPress - Version améliorée"""
    try:
        print(f"\n" + "="*50)
        print(f"📥 UPLOAD WORDPRESS REÇU")
        print(f"   Fichier: {file.filename}")
        print(f"   User ID: {wp_user_id}")
        print(f"   Offer ID: {wp_offer_id}")
        print(f"   Message: {message[:50]}..." if message else "   Message: (aucun)")
        
        if not file.filename:
            raise HTTPException(400, "Nom de fichier requis")
        
        file_content = await file.read()
        print(f"   Taille: {len(file_content)} bytes")
        
        # Extraire le texte
        text = cv_extractor.extract_text(file_content, file.filename)
        print(f"   Texte extrait: {len(text)} caractères")
        
        if not text or len(text.strip()) < 50:
            print("⚠️ Texte insuffisant")
            return {
                "success": True,
                "warning": "Texte insuffisant pour analyse",
                "extracted": {
                    "name": "Candidat",
                    "email": "",
                    "phone": "",
                    "skills": []
                }
            }
        
        # Analyser le CV
        print("🔍 Analyse du CV en cours...")
        result = cv_extractor.analyze_cv(text, file.filename)
        extracted = result.get("extracted", {})
        
        print(f"📊 RÉSULTATS EXTRACTION:")
        print(f"   Nom: {extracted.get('name')}")
        print(f"   Email: {extracted.get('email')}")
        print(f"   Téléphone: {extracted.get('phone')}")
        print(f"   Localisation: {extracted.get('location')}")
        print(f"   Compétences: {len(extracted.get('skills', []))}")
        print(f"   Langues: {len(extracted.get('languages', []))}")
        print(f"   Expérience: {extracted.get('experience_years', 0)} ans")
        print(f"   Niveau: {extracted.get('experience_level')}")
        print(f"   Formation: {extracted.get('education_degree')}")
        print(f"   Métiers: {extracted.get('metiers')}")
        
        # Calculer le hash
        file_hash = hashlib.md5(file_content).hexdigest()
        
        # Sauvegarder dans Supabase
        save_result = {}
        if supabase_manager.client:
            print("💾 Sauvegarde dans Supabase...")
            save_result = supabase_manager.save_candidate(
                cv_data=result,
                file_hash=file_hash,
                filename=file.filename,
                wp_user_id=wp_user_id,
                wp_offer_id=wp_offer_id,
                message=message
            )
            print(f"   Résultat sauvegarde: {save_result.get('success', False)}")
            if save_result.get("error"):
                print(f"   Erreur: {save_result.get('error')}")
        
        # Préparer la réponse
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
        
        print("✅ Traitement terminé avec succès")
        print("="*50 + "\n")
        
        return response
        
    except Exception as e:
        print(f"❌ ERREUR WordPress: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/test-supabase")
async def test_supabase():
    """Test Supabase avec vérification"""
    if not supabase_manager.client:
        return {"connected": False, "error": "Client non initialisé"}
    
    try:
        # Tester la connexion et lire quelques données
        response = supabase_manager.client.table("candidats").select("*").order("created_at", desc=True).limit(3).execute()
        
        candidates_info = []
        if response.data:
            for candidate in response.data:
                candidates_info.append({
                    "id": candidate.get("id"),
                    "nom": candidate.get("nom"),
                    "email": candidate.get("email"),
                    "competences": candidate.get("competences", "")[:50] + "..." if candidate.get("competences") else "vide"
                })
        
        return {
            "connected": True,
            "supabase_url": SUPABASE_URL,
            "test": "success",
            "recent_candidates": candidates_info,
            "total_count": len(response.data) if response.data else 0
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}

# ========== POINT D'ENTRÉE ==========
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"\n" + "="*50)
    print(f"🚀 TruthTalent API Advanced démarrée")
    print(f"   Port: {port}")
    print(f"   PDF support: {PDF_AVAILABLE}")
    print(f"   DOCX support: {DOCX_AVAILABLE}")
    print(f"   Supabase: {SUPABASE_AVAILABLE and bool(SUPABASE_KEY)}")
    print(f"   Extraction: PRÊTE")
    print("="*50 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1
    )