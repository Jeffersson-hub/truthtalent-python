"""
Truth Talent CV Parser API - Déployé sur Vercel
"""

import json
import hashlib
import re
from datetime import datetime
import os
import sys

# AJOUTE CE CODE AU DÉBUT de api/index.py
def handler(request):
    # Extraire le path de la requête
    path = request.path if hasattr(request, 'path') else '/'
    
    # Si c'est la racine ou /api/, traiter normalement
    if path == '/' or path.startswith('/api/'):
        return main_handler(request)
    else:
        # Pour les autres routes, retourner 404
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Not found'})
        }

def main_handler(request):
    # LE RESTE DE TON CODE ACTUEL ICI...
    # (tout ce que tu as déjà dans ta fonction handler)
    
    # Headers CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    # ... reste du code inchangé ...
    
# === FONCTIONS AUXILIAIRES ===

def parse_multipart_form_data(body, boundary):
    """Parse multipart form data manuellement"""
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

# === PARSER DE CV ===

class CVParser:
    
    @staticmethod
    def extract_text_from_pdf(pdf_content):
        """Extrait le texte d'un PDF"""
        try:
            import pdfplumber
            import io
            
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                return full_text
        except Exception as e:
            print(f"⚠️ pdfplumber: {e}")
            return "PDF - Extraction texte requiert pdfplumber"
    
    @staticmethod
    def parse_pdf_content(pdf_content):
        text = CVParser.extract_text_from_pdf(pdf_content)
        return CVParser.parse_text(text)
    
    @staticmethod
    def parse_text(text):
        data = {
            'nom': '', 'prenom': '', 'email': '', 'telephone': '',
            'adresse': '', 'competences': [], 'experiences': [],
            'formations': [], 'langues': [], 'metiers': '',
            'entreprise': '', 'postes': '', 'profil': '',
            'niveau': 'Confirmé', 'annees_experience': 0.0,
            'linkedin': '', 'raw_text': text[:5000],
            'confidence_score': 0.0
        }
        
        try:
            # Nom
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
            
            # Métiers
            metiers = []
            if 'chef de projet' in text.lower(): metiers.append('chef_projet')
            if 'erp' in text.lower(): metiers.append('erp')
            if 'développeur' in text.lower(): metiers.append('developpeur')
            if 'devops' in text.lower(): metiers.append('devops')
            data['metiers'] = ','.join(metiers[:3])
            
            # Expériences
            experiences = []
            exp_pattern = r'(\d{4})\s*[–\-]\s*(.+?)(?=\d{4}|\n\n)'
            for match in re.finditer(exp_pattern, text, re.DOTALL):
                year = match.group(1)
                content = match.group(2).strip()
                entreprise = content.split('(')[1].split(')')[0] if '(' in content else ''
                experiences.append({
                    'periode': year,
                    'entreprise': entreprise,
                    'poste': content.split('-')[0].strip() if '-' in content else content[:50]
                })
            data['experiences'] = experiences
            
            # Formations
            formations = []
            formation_pattern = r'(\d{4})\s*:\s*(.+?)(?=\n\d{4}|\n\n|$)'
            for match in re.finditer(formation_pattern, text, re.DOTALL):
                formations.append({
                    'annee': match.group(1),
                    'diplome': match.group(2).strip()
                })
            data['formations'] = formations
            
            # Compétences
            competences = []
            keywords = ['ERP', 'Python', 'Java', 'SQL', 'AWS', 'Azure', 'Docker',
                       'Agile', 'Scrum', 'Management', 'React', 'Angular', 'Git']
            for kw in keywords:
                if kw in text:
                    competences.append({'nom': kw})
            data['competences'] = competences[:10]
            
            # Langues
            langues = []
            if re.search(r'français', text, re.IGNORECASE):
                langues.append({'langue': 'Français', 'niveau': 'Natif'})
            if re.search(r'anglais', text, re.IGNORECASE):
                langues.append({'langue': 'Anglais', 'niveau': 'Technique'})
            data['langues'] = langues
            
            # Expérience
            if '10 ans' in text or 'dix ans' in text:
                data['annees_experience'] = 10.0
            elif '5 ans' in text or 'cinq ans' in text:
                data['annees_experience'] = 5.0
            
            # Score
            score = 0
            if data['nom']: score += 20
            if data['email']: score += 30
            if data['telephone']: score += 20
            if data['experiences']: score += 20
            if data['competences']: score += 10
            data['confidence_score'] = min(score, 100.0)
            
        except Exception as e:
            print(f"Erreur: {e}")
        
        return data

# === SUPABASE HANDLER ===

class SupabaseHandler:
    
    @staticmethod
    def get_client():
        try:
            from supabase import create_client
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
            
            if not supabase_url or not supabase_key:
                print("⚠️ Variables manquantes")
                return None
            
            return create_client(supabase_url, supabase_key)
        except ImportError:
            print("⚠️ supabase non installé")
            return None
    
    @staticmethod
    def save_candidate(cv_data, file_hash, filename=""):
        client = SupabaseHandler.get_client()
        if not client:
            return {'success': False, 'error': 'Client non disponible'}
        
        try:
            candidate_record = {
                'nom': cv_data.get('nom', ''),
                'prenom': cv_data.get('prenom', ''),
                'email': cv_data.get('email', ''),
                'telephone': cv_data.get('telephone', ''),
                'competences': json.dumps(cv_data.get('competences', []), ensure_ascii=False),
                'experiences': json.dumps(cv_data.get('experiences', []), ensure_ascii=False),
                'formations': json.dumps(cv_data.get('formations', []), ensure_ascii=False),
                'langues': json.dumps(cv_data.get('langues', []), ensure_ascii=False),
                'metiers': cv_data.get('metiers', ''),
                'niveau': cv_data.get('niveau', ''),
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
            
            # Chercher existant
            existing = None
            if cv_data.get('email'):
                existing = client.table('candidats').select('id').eq('email', cv_data['email']).execute()
            
            if (not existing or not existing.data) and file_hash:
                existing = client.table('candidats').select('id').eq('file_hash', file_hash).execute()
            
            if existing and existing.data:
                # Update
                response = client.table('candidats') \
                    .update(candidate_record) \
                    .eq('id', existing.data[0]['id']) \
                    .execute()
                return {
                    'success': True,
                    'action': 'updated',
                    'candidat_id': existing.data[0]['id']
                }
            else:
                # Insert
                response = client.table('candidats') \
                    .insert(candidate_record) \
                    .execute()
                candidat_id = response.data[0]['id'] if response.data else None
                return {
                    'success': True,
                    'action': 'created',
                    'candidat_id': candidat_id
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

# === HANDLER VERCEL ===

def handler(request):
    # Headers CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    # OPTIONS
    if request.method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    # GET
    if request.method == 'GET':
        response = {
            'status': 'online',
            'service': 'Truth Talent CV Parser',
            'version': '1.0',
            'author': 'Jeffersson-hub',
            'endpoints': {'POST /': 'Upload PDF CV', 'GET /': 'Status'}
        }
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response, ensure_ascii=False, indent=2)
        }
    
    # POST
    elif request.method == 'POST':
        try:
            content_type = request.headers.get('content-type', '')
            if 'multipart/form-data' not in content_type:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'error': 'Content-Type multipart requis'})
                }
            
            body = request.body
            if body is None:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'error': 'Body vide'})
                }
            
            if isinstance(body, str):
                body = body.encode('utf-8')
            
            # Boundary
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
                    'body': json.dumps({'success': False, 'error': 'Boundary manquant'})
                }
            
            # Parse
            files = parse_multipart_form_data(body, boundary)
            if 'file' not in files:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'error': 'Aucun fichier'})
                }
            
            filename, file_content = files['file']
            
            # Vérif PDF
            if not filename.lower().endswith('.pdf'):
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'error': 'PDF requis'})
                }
            
            # Taille
            if len(file_content) > 10 * 1024 * 1024:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'success': False, 'error': 'Fichier > 10MB'})
                }
            
            print(f"📥 Fichier: {filename}, {len(file_content)} bytes")
            
            # Hash
            file_hash = hashlib.md5(file_content).hexdigest()
            
            # Parse CV
            cv_data = CVParser.parse_pdf_content(file_content)
            
            # Save to Supabase
            result = SupabaseHandler.save_candidate(cv_data, file_hash, filename)
            
            # Response
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
                    'annees_experience': cv_data.get('annees_experience', 0)
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
            print(f"💥 Erreur: {error_details}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'success': False, 'error': str(e)})
            }
    
    # Autre méthode
    else:
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'success': False, 'error': 'Méthode non autorisée'})
        }