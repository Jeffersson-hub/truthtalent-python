# Modifiez le début du fichier supabase_handler.py
import os
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional

# Import conditionnel pour Vercel
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: supabase not installed")

# Ajoutez ceci pour les logs de debug
import sys
print(f"Python path in supabase_handler: {sys.path}", file=sys.stderr)
print(f"Current directory: {os.getcwd()}", file=sys.stderr)

class SupabaseHandler:
    def __init__(self):
        # Debug: afficher les variables d'environnement disponibles
        env_vars = {k: 'SET' for k in os.environ if 'SUPABASE' in k}
        print(f"Supabase env vars available: {list(env_vars.keys())}", file=sys.stderr)
        
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY', '')
        
        if not self.supabase_url:
            print("ERROR: SUPABASE_URL not set", file=sys.stderr)
        if not self.supabase_key:
            print("ERROR: SUPABASE_SERVICE_KEY not set", file=sys.stderr)
        
        # Continue même si vide pour permettre le démarrage
        if self.supabase_url and self.supabase_key:
            self.client = create_client(self.supabase_url, self.supabase_key)
            print("✅ Supabase client created successfully", file=sys.stderr)
        else:
            self.client = None
            print("⚠️ Supabase client not created - missing credentials", file=sys.stderr)

    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calcule le hash MD5"""
        return hashlib.md5(file_content).hexdigest()
    
    def check_duplicate(self, email: str = None, file_hash: str = None) -> Optional[int]:
        """Vérifie si le candidat existe déjà"""
        query = self.client.table('candidats').select('id')
        
        if email:
            query = query.eq('email', email)
        elif file_hash:
            query = query.eq('file_hash', file_hash)
        else:
            return None
        
        response = query.execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['id']
        
        return None
    
    def save_candidate(self, cv_data: Dict, file_hash: str, filename: str = "") -> Dict:
        """Sauvegarde le candidat dans Supabase"""
        
        # Préparer la donnée pour ta table
        candidate_record = {
            'nom': cv_data.get('nom', ''),
            'prenom': cv_data.get('prenom', ''),
            'email': cv_data.get('email', ''),
            'telephone': cv_data.get('telephone', ''),
            'adresse': cv_data.get('adresse', ''),
            'competences': json.dumps(cv_data.get('competences', []), ensure_ascii=False),
            'experiences': json.dumps(cv_data.get('experiences', []), ensure_ascii=False),
            'formations': json.dumps(cv_data.get('formations', []), ensure_ascii=False),
            'langues': json.dumps(cv_data.get('langues', []), ensure_ascii=False),
            'linkedin': cv_data.get('linkedin', ''),
            'raw_text': cv_data.get('raw_text', '')[:8000],  # Limiter taille
            'metiers': cv_data.get('metiers', ''),
            'entreprise': cv_data.get('entreprise', ''),
            'postes': cv_data.get('postes', ''),
            'profil': cv_data.get('profil', ''),
            'niveau': cv_data.get('niveau', ''),
            'annees_experience': cv_data.get('annees_experience', 0.0),
            'fichier': filename,
            'file_hash': file_hash,
            'cv_filename': filename,
            'status': 'analysé',
            'parse_status': 'success',
            'date_import': datetime.now().isoformat(),
            'date_analyse': datetime.now().isoformat(),
            'confidence_score': cv_data.get('confidence_score', 0.0),
            'source': 'api_python'
        }
        
        # Nettoyer les valeurs None
        for key, value in list(candidate_record.items()):
            if value is None:
                candidate_record[key] = ''
        
        try:
            # Vérifier existence
            existing_id = None
            if cv_data.get('email'):
                existing_id = self.check_duplicate(email=cv_data['email'])
            
            if not existing_id and file_hash:
                existing_id = self.check_duplicate(file_hash=file_hash)
            
            if existing_id:
                # Mise à jour
                response = self.client.table('candidats') \
                    .update(candidate_record) \
                    .eq('id', existing_id) \
                    .execute()
                
                return {
                    'success': True,
                    'action': 'updated',
                    'candidat_id': existing_id,
                    'data': response.data[0] if response.data else None
                }
            else:
                # Insertion
                response = self.client.table('candidats') \
                    .insert(candidate_record) \
                    .execute()
                
                candidat_id = response.data[0]['id'] if response.data else None
                
                return {
                    'success': True,
                    'action': 'created',
                    'candidat_id': candidat_id,
                    'data': response.data[0] if response.data else None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'action': 'error'
            }
    
    def get_candidates(self, limit: int = 50, offset: int = 0):
        """Récupère la liste des candidats"""
        try:
            response = self.client.table('candidats') \
                .select('*') \
                .order('date_import', desc=True) \
                .range(offset, offset + limit - 1) \
                .execute()
            
            return {
                'success': True,
                'data': response.data,
                'count': len(response.data)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }