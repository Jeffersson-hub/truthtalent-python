"""
API Truth Talent - Parser de CV PDF
Point d'entrée unique pour Vercel Serverless Functions
"""

import json
import hashlib
import re
from datetime import datetime

# === FONCTIONS AUXILIAIRES ===

def parse_multipart_form_data(body, boundary):
    """Parse multipart form data manuellement"""
    try:
        parts = body.split(b'--' + boundary.encode())
        files = {}
        
        for part in parts[1:-1]:  # Ignorer le début et la fin
            if b'filename=' in part and b'\r\n\r\n' in part:
                headers, content = part.split(b'\r\n\r\n', 1)
                content = content.rstrip(b'\r\n')
                
                # Extraire le filename
                for line in headers.split(b'\r\n'):
                    if b'filename=' in line:
                        try:
                            filename_part = line.split(b'filename=')[1]
                            filename = filename_part.strip(b'"\r\n').decode('utf-8', errors='ignore')
                            files['file'] = (filename, content)
                            break
                        except:
                            continue
        
        return files
    except Exception as e:
        raise Exception(f"Erreur parsing form-data: {str(e)}")

# === PARSER DE CV ===

class CVParser:
    """Parser de CV tout-en-un"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content):
        """Extrait le texte d'un PDF sans dépendance externe"""
        # Fallback simple - dans un cas réel, utiliserait pdfplumber
        # Pour Vercel, on peut utiliser PyPDF2 ou une API externe
        # Ici, simulation pour démonstration
        return "Texte extrait du PDF - à implémenter avec pdfplumber"
    
    @staticmethod
    def parse_pdf_content(pdf_content):
        """Parse le contenu PDF et extrait les informations"""
        # En production, décommentez ceci :
        # import pdfplumber
        # import io
        # with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        #     text = ""
        #     for page in pdf.pages:
        #         text += page.extract_text() + "\n"
        
        # Pour le test, utiliser un texte exemple
        text = """
        # Jean-François BOISGONTIER
        
        Chef de projet ERP secteur PME
        La Tour-sur-orb – Déplacements à l'international
        0659615166 jf.boisgontier@yahoo.fr
        
        Chef de Projet IT expérimenté, fort de plus de 10 ans d'expérience en gestion de projet.
        
        Compétences
        
        ## Gestion de Projet ERP & Transformation Numérique :
         Pilotage de déploiements ERP
         Conception de stratégies de tests
        
        Expériences Professionnelles
        
        Chef de projet - Crédit Agricole (2024)
         Cadrage des projets et planification
         Pilotage d'équipes applicatives
        
        Ingénieur production - Crédit Agricole (2023)
         Infrastructure Sonarqube pour flux des données
        
        Formations
        
        • 2020 : Concepteur Développeur d'Applications, LDNR Labège (Java, Angular)
        • 2012 : Chef de Projet Informatique, CESI Labège
        """
        
        return CVParser.parse_text(text)
    
    @staticmethod
    def parse_text(text):
        """Parse le texte d'un CV"""
        data = {
            'nom': '',
            'prenom': '',
            'email': '',
            'telephone': '',
            'adresse': '',
            'competences': [],
            'experiences': [],
            'formations': [],
            'langues': [],
            'metiers': '',
            'entreprise': '',
            'postes': '',
            'profil': '',
            'niveau': 'Confirmé',
            'annees_experience': 0.0,
            'linkedin': '',
            'raw_text': text[:5000],
            'confidence_score': 0.0
        }
        
        try:
            # Extraire nom (première ligne non vide)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                data['nom'] = lines[0]
                # Extraire prénom (premier mot)
                parts = data['nom'].split()
                if parts:
                    data['prenom'] = parts[0]
            
            # Extraire email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if email_match:
                data['email'] = email_match.group(0)
            
            # Extraire téléphone
            tel_match = re.search(r'(?:\+33|0)[1-9](?:[\.\-\s]?\d{2}){4}', text)
            if tel_match:
                data['telephone'] = tel_match.group(0)
            
            # Extraire ville
            ville_match = re.search(r'[\w\s-]+(?=\s*[–\-]\s*)', text[:500])
            if ville_match:
                data['adresse'] = ville_match.group(0).strip()
            
            # Détecter métiers
            metiers = []
            if 'chef de projet' in text.lower():
                metiers.append('chef_projet')
            if 'erp' in text.lower():
                metiers.append('erp')
            if 'développeur' in text.lower():
                metiers.append('developpeur')
            data['metiers'] = ','.join(metiers[:3])
            
            # Extraire expériences
            exp_pattern = r'(\d{4})\s*[–\-]\s*(.+?)(?=\d{4}|\n\n)'
            experiences = []
            for match in re.finditer(exp_pattern, text, re.DOTALL):
                year = match.group(1)
                content = match.group(2).strip()
                
                # Chercher entreprise
                entreprise = ''
                if '(' in content:
                    entreprise = content.split('(')[1].split(')')[0]
                
                experiences.append({
                    'periode': year,
                    'entreprise': entreprise,
                    'poste': content.split('-')[0].strip() if '-' in content else content[:50]
                })
            
            data['experiences'] = experiences
            
            # Extraire formations
            formations = []
            formation_pattern = r'(\d{4})\s*:\s*(.+?)(?=\n\d{4}|\n\n|$)'
            for match in re.finditer(formation_pattern, text, re.DOTALL):
                year = match.group(1)
                details = match.group(2).strip()
                formations.append({
                    'annee': year,
                    'diplome': details
                })
            
            data['formations'] = formations
            
            # Compétences (mots-clés)
            competences = []
            keywords = ['ERP', 'Python', 'Java', 'SQL', 'AWS', 'Azure', 'Docker', 
                       'Agile', 'Scrum', 'Management', 'Gestion de projet']
            for kw in keywords:
                if kw in text:
                    competences.append({'nom': kw})
            
            data['competences'] = competences
            
            # Langues
            langues = []
            if re.search(r'français', text, re.IGNORECASE):
                langues.append({'langue': 'Français', 'niveau': 'Natif'})
            if re.search(r'anglais', text, re.IGNORECASE):
                langues.append({'langue': 'Anglais', 'niveau': 'Technique'})
            
            data['langues'] = langues
            
            # Années d'expérience
            if '10 ans' in text or 'dix ans' in text:
                data['annees_experience'] = 10.0
            elif '5 ans' in text or 'cinq ans' in text:
                data['annees_experience'] = 5.0
            
            # Score de confiance
            score = 0
            if data['nom']: score += 20
            if data['email']: score += 30
            if data['telephone']: score += 20
            if data['experiences']: score += 30
            data['confidence_score'] = min(score, 100.0)
            
        except Exception as e:
            print(f"Erreur parsing: {e}")
        
        return data

# === SUPABASE HANDLER (SIMPLIFIÉ) ===

class SupabaseHandler:
    """Handler Supabase simplifié pour Vercel"""
    
    @staticmethod
    def save_candidate_simple(cv_data, file_hash, filename=""):
        """
        Version simplifiée qui retourne un succès simulé
        En production, décommentez le code Supabase réel
        """
        try:
            # SIMULATION - En production, utiliser le vrai client Supabase
            
            # Décommentez ceci pour la version réelle :
            """
            import os
            from supabase import create_client
            
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
            
            if not supabase_url or not supabase_key:
                return {'success': False, 'error': 'Configuration manquante'}
            
            client = create_client(supabase_url, supabase_key)
            
            candidate_record = {
                'nom': cv_data.get('nom', ''),
                'email': cv_data.get('email', ''),
                'telephone': cv_data.get('telephone', ''),
                'competences': json.dumps(cv_data.get('competences', [])),
                'experiences': json.dumps(cv_data.get('experiences', [])),
                'formations': json.dumps(cv_data.get('formations', [])),
                'metiers': cv_data.get('metiers', ''),
                'annees_experience': cv_data.get('annees_experience', 0),
                'fichier': filename,
                'file_hash': file_hash,
                'status': 'analysé',
                'confidence_score': cv_data.get('confidence_score', 0),
                'date_import': datetime.now().isoformat()
            }
            
            # Insertion dans Supabase
            response = client.table('candidats').insert(candidate_record).execute()
            
            return {
                'success': True,
                'action': 'created',
                'candidat_id': response.data[0]['id'] if response.data else None
            }
            """
            
            # Version simulation pour test
            return {
                'success': True,
                'action': 'created',
                'candidat_id': 'sim123',
                'message': 'CV analysé avec succès (mode simulation)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Erreur Supabase: {str(e)}"
            }

# === HANDLER VERCEL PRINCIPAL ===

def handler(request):
    """
    Handler principal pour Vercel Serverless Functions
    Format: https://vercel.com/docs/functions/serverless-functions/runtimes/python
    """
    
    # Headers CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    # Gestion OPTIONS (CORS preflight)
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # GET - Page d'accueil / test
    if request.method == 'GET':
        response = {
            'status': 'online',
            'service': 'Truth Talent CV Parser API',
            'version': '1.0.0',
            'endpoints': {
                'POST /': 'Upload et analyse de CV PDF',
                'GET /': 'Cette page de statut'
            },
            'instructions': 'Envoyez un POST avec un fichier PDF en multipart/form-data'
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response, ensure_ascii=False, indent=2)
        }
    
    # POST - Upload de CV
    elif request.method == 'POST':
        try:
            # Vérifier content-type
            content_type = request.headers.get('content-type', '')
            
            if not content_type or 'multipart/form-data' not in content_type:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Content-Type doit être multipart/form-data'
                    }, ensure_ascii=False)
                }
            
            # Récupérer le body
            body = request.body
            if body is None:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Body vide'
                    }, ensure_ascii=False)
                }
            
            # Convertir en bytes si nécessaire
            if isinstance(body, str):
                body = body.encode('utf-8')
            
            # Extraire boundary
            boundary = None
            for part in content_type.split(';'):
                part = part.strip()
                if part.startswith('boundary='):
                    boundary = part[9:]
                    break
            
            if not boundary:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Boundary non trouvé'
                    }, ensure_ascii=False)
                }
            
            # Parser le form-data
            files = parse_multipart_form_data(body, boundary)
            
            if 'file' not in files:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Aucun fichier uploadé'
                    }, ensure_ascii=False)
                }
            
            filename, file_content = files['file']
            
            # Vérifier que c'est un PDF
            if not filename.lower().endswith('.pdf'):
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Le fichier doit être un PDF'
                    }, ensure_ascii=False)
                }
            
            # Vérifier taille (max 10MB)
            if len(file_content) > 10 * 1024 * 1024:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Fichier trop volumineux (max 10MB)'
                    }, ensure_ascii=False)
                }
            
            print(f"Fichier reçu: {filename}, taille: {len(file_content)} bytes")
            
            # Calculer hash
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Parser le PDF
            cv_data = CVParser.parse_pdf_content(file_content)
            
            # Sauvegarder dans Supabase
            result = SupabaseHandler.save_candidate_simple(cv_data, file_hash, filename)
            
            # Construire la réponse
            response = {
                'success': result.get('success', False),
                'action': result.get('action', 'unknown'),
                'candidat_id': result.get('candidat_id'),
                'confidence_score': cv_data.get('confidence_score', 0),
                'extracted_data': {
                    'nom': cv_data.get('nom', ''),
                    'email': cv_data.get('email', ''),
                    'telephone': cv_data.get('telephone', ''),
                    'metiers': cv_data.get('metiers', ''),
                    'annees_experience': cv_data.get('annees_experience', 0),
                    'competences_count': len(cv_data.get('competences', [])),
                    'experiences_count': len(cv_data.get('experiences', []))
                }
            }
            
            if not result['success']:
                response['error'] = result.get('error', 'Erreur inconnue')
            
            status_code = 200 if result['success'] else 500
            
            return {
                'statusCode': status_code,
                'headers': headers,
                'body': json.dumps(response, ensure_ascii=False, indent=2)
            }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Erreur détaillée: {error_details}")
            
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': f"Erreur serveur: {str(e)}"
                }, ensure_ascii=False)
            }
    
    # Méthode non supportée
    else:
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Méthode non autorisée'
            }, ensure_ascii=False)
        }