#!/usr/bin/env python3
"""
Advanced CV Parser avec extraction intelligente
Amélioration de parseur.com
"""
import re
import json
from typing import Dict, List, Optional, Tuple
import spacy
from dateutil import parser as date_parser
from datetime import datetime
import io

try:
    # Essayer de charger le modèle français
    nlp = spacy.load("fr_core_news_sm")
    SPACY_AVAILABLE = True
except:
    try:
        # Charger le modèle anglais en fallback
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except:
        SPACY_AVAILABLE = False
        print("⚠️ SpaCy non disponible - extraction limitée")

class AdvancedCVParser:
    """Parser avancé de CV avec NLP"""
    
    def __init__(self):
        self.skills_db = self.load_skills_database()
        
    def load_skills_database(self) -> Dict:
        """Base de données de compétences par domaine"""
        return {
            "backend": ["Python", "Java", "C#", "PHP", "Ruby", "Node.js", "Go", "Rust"],
            "frontend": ["JavaScript", "TypeScript", "React", "Vue.js", "Angular", "Svelte"],
            "devops": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform", "Jenkins"],
            "mobile": ["Swift", "Kotlin", "Flutter", "React Native"],
            "database": ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch"],
            "data_science": ["Python", "R", "TensorFlow", "PyTorch", "Pandas", "NumPy"],
            "design": ["Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator"],
            "soft_skills": ["Communication", "Leadership", "Travail d'équipe", "Proactivité"]
        }
    
    def parse_cv_advanced(self, text: str, filename: str = "") -> Dict:
        """Analyse avancée du CV avec NLP"""
        result = {
            "personal_info": {},
            "experience": [],
            "education": [],
            "skills": {},
            "summary": "",
            "confidence_score": 0.0,
            "metadata": {}
        }
        
        # Nettoyer le texte
        clean_text = self.clean_text(text)
        
        # Extraction avec NLP si disponible
        if SPACY_AVAILABLE and len(clean_text) > 100:
            doc = nlp(clean_text[:10000])  # Limiter pour performance
            
            # Extraire les entités nommées
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
            
            result["entities"] = entities
            
            # Extraire les phrases clés
            key_sentences = []
            for sent in doc.sents:
                if len(sent.text.split()) > 5 and len(sent.text.split()) < 30:
                    # Vérifier si la phrase contient des mots importants
                    important_words = ["expérience", "compétence", "projet", "réalisé", "développé"]
                    if any(word in sent.text.lower() for word in important_words):
                        key_sentences.append(sent.text)
            
            result["key_sentences"] = key_sentences[:5]
        
        # Extraction structurée
        result.update(self.extract_personal_info(clean_text))
        result["experience"] = self.extract_experience(clean_text)
        result["education"] = self.extract_education(clean_text)
        result["skills"] = self.extract_skills_advanced(clean_text)
        result["summary"] = self.extract_summary(clean_text)
        
        # Calculer le score de confiance
        confidence = self.calculate_confidence(result)
        result["confidence_score"] = confidence
        
        # Métadonnées
        result["metadata"] = {
            "source": filename,
            "char_count": len(text),
            "word_count": len(text.split()),
            "processing_date": datetime.now().isoformat(),
            "parser_version": "2.0"
        }
        
        return result
    
    def clean_text(self, text: str) -> str:
        """Nettoyer le texte"""
        # Supprimer les caractères spéciaux multiples
        text = re.sub(r'\s+', ' ', text)
        # Normaliser les retours à la ligne
        text = re.sub(r'\n+', '\n', text)
        # Supprimer les espaces en début/fin
        text = text.strip()
        return text
    
    def extract_personal_info(self, text: str) -> Dict:
        """Extraire les informations personnelles"""
        info = {
            "full_name": "",
            "first_name": "",
            "last_name": "",
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
        
        # Téléphone (format français/international)
        phone_patterns = [
            r'(\+33\s?|0)[1-9]([\s.-]?\d{2}){4}',
            r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',
            r'\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2}[.\s]?\d{2}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                info["phone"] = phones[0] if isinstance(phones[0], str) else phones[0][0]
                break
        
        # LinkedIn
        linkedin_patterns = [
            r'linkedin\.com/in/[a-zA-Z0-9-]+',
            r'linkedin\.com/company/[a-zA-Z0-9-]+'
        ]
        
        for pattern in linkedin_patterns:
            linkedins = re.findall(pattern, text)
            if linkedins:
                info["linkedin"] = "https://" + linkedins[0]
                break
        
        # Localisation (villes françaises)
        french_cities = ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes", 
                        "Strasbourg", "Montpellier", "Bordeaux", "Lille"]
        
        for city in french_cities:
            if city in text:
                info["location"] = city
                break
        
        # Nom complet (première ligne significative)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines[:5]:
            if len(line) > 3 and len(line) < 50:
                if not any(word in line.lower() for word in ['email', 'phone', 'tel', 'cv', 'resume', '@']):
                    info["full_name"] = line
                    
                    # Tenter de séparer prénom/nom
                    parts = line.split()
                    if len(parts) >= 2:
                        info["first_name"] = parts[0]
                        info["last_name"] = " ".join(parts[1:])
                    break
        
        return info
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extraire les expériences professionnelles"""
        experiences = []
        
        # Chercher des sections d'expérience
        exp_keywords = ["expérience", "experience", "expériences", "experiences", 
                       "professionnel", "professionnelle", "emploi", "travail"]
        
        lines = text.split('\n')
        in_exp_section = False
        current_exp = {}
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Détecter début d'une expérience
            exp_patterns = [
                r'(\d{4})\s*[-–]\s*(?:présent|\d{4})',  # 2020 - 2023
                r'(\w+\s+\d{4})\s*[-–]\s*(?:présent|\w+\s+\d{4})',  # Jan 2020 - Dec 2023
                r'chez\s+[A-Z]',  # chez Google
                r'[A-Z][a-z]+\s+(?:SAS|SA|SARL|EURL)'  # Nom d'entreprise
            ]
            
            for pattern in exp_patterns:
                if re.search(pattern, line):
                    if current_exp and len(current_exp) > 0:
                        experiences.append(current_exp)
                    
                    current_exp = {
                        "position": line.strip(),
                        "company": "",
                        "period": "",
                        "description": []
                    }
                    in_exp_section = True
                    break
            
            # Collecter la description
            elif in_exp_section and line.strip() and len(line.strip()) > 10:
                if "description" not in current_exp:
                    current_exp["description"] = []
                current_exp["description"].append(line.strip())
        
        # Ajouter la dernière expérience
        if current_exp and len(current_exp) > 0:
            experiences.append(current_exp)
        
        return experiences[:10]  # Limiter à 10 expériences
    
    def extract_education(self, text: str) -> List[Dict]:
        """Extraire les formations"""
        education = []
        
        edu_keywords = ["éducation", "education", "formation", "formations", 
                       "diplôme", "diplome", "bac", "master", "licence", "école", "université"]
        
        lines = text.split('\n')
        in_edu_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Vérifier si la ligne contient un mot-clé d'éducation
            if any(keyword in line_lower for keyword in edu_keywords):
                if i + 1 < len(lines):
                    education_entry = {
                        "degree": line.strip(),
                        "school": lines[i + 1].strip() if i + 1 < len(lines) else "",
                        "year": self.extract_year_from_text(line)
                    }
                    education.append(education_entry)
        
        return education[:5]
    
    def extract_skills_advanced(self, text: str) -> Dict:
        """Extraction avancée des compétences par catégorie"""
        skills_found = {category: [] for category in self.skills_db.keys()}
        text_lower = text.lower()
        
        for category, skill_list in self.skills_db.items():
            for skill in skill_list:
                # Rechercher la compétence (insensible à la casse)
                if skill.lower() in text_lower:
                    skills_found[category].append(skill)
        
        # Extraire les compétences spécifiques au CV
        specific_patterns = {
            "certifications": r'(?:certification|certificat)\s+(?:en\s+)?([A-Z][a-zA-Z\s]+)',
            "languages": r'(?:anglais|français|espagnol|allemand|italien)\s*(?:\(([A-C1-3\+]+)\))?',
            "tools": r'(?:Jira|Confluence|GitLab|GitHub|Notion|Slack|Teams)'
        }
        
        for category, pattern in specific_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                skills_found[category] = list(set(matches))
        
        # Nettoyer les catégories vides
        return {k: v for k, v in skills_found.items() if v}
    
    def extract_summary(self, text: str) -> str:
        """Extraire un résumé/objectif"""
        summary_keywords = ["résumé", "summary", "profil", "profile", 
                           "objectif", "objective", "à propos", "about"]
        
        lines = text.split('\n')
        summary_lines = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in summary_keywords):
                # Prendre les 3 lignes suivantes
                for j in range(i + 1, min(i + 4, len(lines))):
                    if lines[j].strip() and len(lines[j].strip()) > 10:
                        summary_lines.append(lines[j].strip())
                break
        
        if summary_lines:
            return " ".join(summary_lines)
        
        # Fallback: première phrase significative
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) > 5 and len(sentence.split()) < 30:
                return sentence
        
        return ""
    
    def extract_year_from_text(self, text: str) -> str:
        """Extraire une année depuis un texte"""
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            return year_match.group()
        return ""
    
    def calculate_confidence(self, result: Dict) -> float:
        """Calculer un score de confiance"""
        score = 0.0
        
        # Points pour chaque information trouvée
        if result["personal_info"].get("email"):
            score += 0.2
        if result["personal_info"].get("phone"):
            score += 0.15
        if result["personal_info"].get("full_name"):
            score += 0.15
        if result.get("experience") and len(result["experience"]) > 0:
            score += 0.25
        if result.get("skills") and len(result["skills"]) > 0:
            score += 0.15
        if result.get("education") and len(result["education"]) > 0:
            score += 0.1
        
        return min(score, 1.0)

# Singleton pour éviter de charger le modèle à chaque requête
advanced_parser = AdvancedCVParser()