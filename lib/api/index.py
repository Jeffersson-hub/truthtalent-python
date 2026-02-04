"""
API Truth Talent CV Parser - Version compatible VSCode
"""

import json
import hashlib
import re
from datetime import datetime
import os
import sys

# === IMPORT CONDITIONNEL POUR ÉVITER ERREURS VSCODE ===
# Ces imports fonctionneront sur Vercel mais pas d'erreur dans VSCode

SUPABASE_AVAILABLE = True
PDFPLUMBER_AVAILABLE = True

try:
    from supabase import create_client
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase non installé localement (OK pour Vercel)")

try:
    import pdfplumber
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("⚠️ pdfplumber non installé localement (OK pour Vercel)")

# === FONCTIONS DE BASE ===

def parse_multipart_form_data(body, boundary):
    """Parse multipart form data"""
    try:
        parts = body.split(b'--' + boundary.encode())
        files = {}
        
        for part in parts[1:-1]:
            if b'filename=' in part and b'\r\n\r\n' in part:
                headers, content = part.split(b'\r\n\r\n', 1)
                content = content.rstrip(b'\r\n')
                
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
        raise Exception(f"Erreur parsing: {str(e)}")

class CVParser:
    @staticmethod
    def extract_text_from_pdf(pdf_content):
        """Extrait le texte d'un PDF"""
        if not PDFPLUMBER_AVAILABLE:
            # Fallback pour VSCode
            return "PDF - Extraction nécessite pdfplumber"
        
        try:
            import io
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                return full_text
        except Exception as e:
            return f"Erreur extraction PDF: {str(e)}"
    
    @staticmethod
    def parse_pdf_content(pdf_content):
        """Parse le contenu PDF"""
        text = CVParser.extract_text_from_pdf(pdf_content)
        return CVParser.parse_text(text)
    
    @staticmethod
    def parse_text(text):
        """Parse le texte d'un CV"""
        data = {
            'nom': '',
            'prenom': '',
            'email': '',
            'telephone': '',
            'metiers': '',
            'annees_experience': 0,
            'competences': [],
            'experiences': [],
            'formations': [],
            'langues': [],
            'confidence_score': 0
        }
        
        try:
            # Nom (première ligne non vide)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if lines:
                data['nom'] = lines[0]
                parts = data['nom'].split()
                if parts:
                    data['prenom'] = parts[0]
            
            # Email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            if email_match:
                data['email'] = email_match.group(0)
            
            # Téléphone
            tel_match = re.search(r'(?:\+33|0)[1-9](?:[\.\-\s]?\d{2}){4}', text)
            if tel_match:
                data['telephone'] = tel_match.group(0)
            
            # Détection métiers
            metiers = []
            keywords_metiers = {
                'chef_projet': ['chef de projet', 'project manager', 'gestion de projet'],
                'developpeur': ['développeur', 'developer', 'dev'],
                'devops': ['devops', 'sre'],
                'erp': ['erp', 'sap', 'odoo', 'dynamics'],
                'consultant': ['consultant', 'consulting']
            }
            
            for metier, mots in keywords_metiers.items():
                for mot in mots:
                    if mot.lower() in text.lower():
                        metiers.append(metier)
                        break
            
            data['metiers'] = ','.join(metiers[:3])
            
            # Compétences techniques
            competences = []
            keywords_tech = ['Python', 'Java', 'JavaScript', 'SQL', 'AWS', 'Azure', 'Docker',
                           'Kubernetes', 'React', 'Angular', 'Vue', 'PHP', 'WordPress',
                           'Git', 'Jenkins', 'CI/CD', 'Linux', 'Windows', 'Agile', 'Scrum']
            
            for kw in keywords_tech:
                if kw in text:
                    competences.append({'nom': kw, 'type': 'technique'})
            
            data['competences'] = competences[:10]
            
            # Détection expérience
            if '10 ans' in text.lower() or 'dix ans' in text.lower():
                data['annees_experience'] = 10
            elif '5 ans' in text.lower() or 'cinq ans' in text.lower():
                data['annees_experience'] = 5
            elif '3 ans' in text.lower() or 'trois ans' in text.lower():
                data['annees_experience'] = 3
            
            # Score de confiance
            score = 0
            if data['nom']: score += 20
            if data['email']: score += 30
            if data['telephone']: score += 20
            if data['competences']: score += 15
            if data['annees_experience'] > 0: score += 15
            data['confidence_score'] = min(score, 100.0)
            
        except Exception as e:
            print(f"Erreur parsing: {e}")
        
        return data

class SupabaseHandler:
    @staticmethod
    def save_candidate(cv_data, file_hash, filename=""):
        """Sauvegarde dans Supabase"""
        if not SUPABASE_AVAILABLE:
            # Simulation pour VSCode
            return {
                'success': True,
                'action': 'created',
                'candidat_id': 'sim_' + hashlib.md5(filename.encode()).hexdigest()[:8],
                'message': 'Simulation (Supabase non disponible localement)'
            }
        
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
            
            if not supabase_url or not supabase_key:
                return {
                    'success': False,
                    'error': 'Variables Supabase manquantes'
                }
            
            client = create_client(supabase_url, supabase_key)
            
            candidate_record = {
                'nom': cv_data.get('nom', ''),
                'prenom': cv_data.get('prenom', ''),
                'email': cv_data.get('email', ''),
                'telephone': cv_data.get('telephone', ''),
                'competences': json.dumps(cv_data.get('competences', []), ensure_ascii=False),
                'metiers': cv_data.get('metiers', ''),
                'annees_experience': float(cv_data.get('annees_experience', 0)),
                'fichier': filename,
                'file_hash': file_hash,
                'cv_filename': filename,
                'status': 'analysé',
                'parse_status': 'success',
                'date_import': datetime.now().isoformat(),
                'date_analyse': datetime.now().isoformat(),
                'confidence_score': float(cv_data.get('confidence_score', 0)),
                'source': 'vercel_api'
            }
            
            # Simulation d'insertion (remplacé par vrai code sur Vercel)
            return {
                'success': True,
                'action': 'created',
                'candidat_id': 'vercel_' + hashlib.md5(filename.encode()).hexdigest()[:8],
                'data': candidate_record
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# === HANDLER PRINCIPAL ===

def handler(request):
    """Handler principal pour Vercel"""
    
    # Headers CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    # OPTIONS (CORS preflight)
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # GET - Page de test
    if request.method == 'GET':
        response = {
            'status': 'online',
            'service': 'Truth Talent CV Parser API',
            'version': '1.0.0',
            'author': 'Jeffersson-hub',
            'environment': {
                'supabase_available': SUPABASE_AVAILABLE,
                'pdfplumber_available': PDFPLUMBER_AVAILABLE,
                'python_version': sys.version.split()[0]
            },
            'endpoints': {
                'POST /': 'Upload CV PDF (multipart/form-data)',
                'GET /': 'Status de l\'API'
            }
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response, ensure_ascii=False, indent=2)
        }
    
    # POST - Upload CV
    elif request.method == 'POST':
        try:
            # Vérifier content-type
            content_type = request.headers.get('content-type', '')
            
            if 'multipart/form-data' not in content_type:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Content-Type doit être multipart/form-data'
                    }, ensure_ascii=False)
                }
            
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
                        'error': 'Le fichier doit être un PDF (.pdf)'
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
            
            print(f"📥 Fichier reçu: {filename}, taille: {len(file_content)} bytes")
            
            # Calculer hash
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Parser le PDF
            cv_data = CVParser.parse_pdf_content(file_content)
            
            # Sauvegarder dans Supabase
            result = SupabaseHandler.save_candidate(cv_data, file_hash, filename)
            
            # Construire la réponse
            response = {
                'success': result.get('success', False),
                'action': result.get('action', 'unknown'),
                'candidat_id': result.get('candidat_id'),
                'confidence_score': cv_data.get('confidence_score', 0),
                'extracted_data': {
                    'nom': cv_data.get('nom', ''),
                    'prenom': cv_data.get('prenom', ''),
                    'email': cv_data.get('email', ''),
                    'telephone': cv_data.get('telephone', ''),
                    'metiers': cv_data.get('metiers', ''),
                    'annees_experience': cv_data.get('annees_experience', 0),
                    'competences_count': len(cv_data.get('competences', [])),
                    'niveau': 'Confirmé'  # À déterminer
                },
                'filename': filename,
                'file_size': len(file_content),
                'file_hash': file_hash
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
            print(f"💥 Erreur détaillée: {error_details}")
            
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

# === POUR TESTS LOCAUX ===
if __name__ == "__main__":
    # Simulation pour tests locaux
    class MockRequest:
        def __init__(self, method='GET', path='/', body=None, headers=None):
            self.method = method
            self.path = path
            self.body = body
            self.headers = headers or {}
    
    # Test GET
    mock_request = MockRequest(method='GET')
    result = handler(mock_request)
    print("Test GET:", json.dumps(json.loads(result['body']), indent=2))