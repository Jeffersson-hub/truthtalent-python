#!/usr/bin/env python3
"""
TruthTalent API - Format AWS Lambda POUR VERCEL
NOUS NE SOMMES PAS UN SERVEUR HTTP, MAIS UNE FONCTION LAMBDA
"""
import json
import base64
from datetime import datetime

# === HANDLER AWS LAMBDA ===
# DOIT s'appeler "handler" et prendre (event, context)
def handler(event, context):
    """
    Handler AWS Lambda - LE SEUL FORMAT QUE VERCEL COMPREND
    """
    print("🚀 Handler Lambda appelé par Vercel")
    
    # 1. DÉBOGUER - voir ce que Vercel nous envoie
    print("📥 Event reçu:", json.dumps(event, indent=2)[:500])
    
    # 2. Extraire méthode HTTP et chemin
    # Format Vercel 2.0
    http_info = event.get('requestContext', {}).get('http', {})
    http_method = http_info.get('method', event.get('httpMethod', 'GET'))
    path = http_info.get('path', event.get('path', '/'))
    
    print(f"🔍 Method: {http_method}, Path: {path}")
    
    # 3. HEADERS CORS ABSOLUS
    cors_headers = {
        'Access-Control-Allow-Origin': 'https://truthtalent.online',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin',
        'Access-Control-Max-Age': '86400',
        'Vary': 'Origin'
    }
    
    # 4. GÉRER OPTIONS (CORS PRE-FLIGHT)
    if http_method == 'OPTIONS':
        print("🔧 Réponse OPTIONS pour CORS")
        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': ''
        }
    
    # 5. AJOUTER Content-Type pour les réponses JSON
    response_headers = {**cors_headers, 'Content-Type': 'application/json'}
    
    # 6. ROUTES
    if http_method == 'GET' and path == '/':
        response_body = {
            'api': 'TruthTalent',
            'status': 'RUNNING',
            'message': 'API fonctionne sur Vercel avec CORS',
            'timestamp': datetime.now().isoformat(),
            'cors': 'configuré pour https://truthtalent.online',
            'endpoints': ['GET /', 'POST /jobs', 'OPTIONS /*']
        }
        
        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps(response_body, indent=2)
        }
    
    elif http_method == 'POST' and path == '/jobs':
        try:
            print("📨 POST /jobs reçu")
            
            # Décoder le body si base64
            body = event.get('body', '{}')
            if event.get('isBase64Encoded', False):
                body = base64.b64decode(body).decode('utf-8', errors='ignore')
            
            print(f"📄 Body ({len(body)} chars): {body[:200]}...")
            
            # SIMULER le parsing d'un CV
            # (Vous ajouterez le vrai parsing plus tard)
            response_body = {
                'success': True,
                'message': 'CV traité avec succès',
                'action': 'analysé et sauvegardé',
                'data': {
                    'email': 'extrait@example.com',
                    'nom': 'Candidat Extraits',
                    'competences': ['Python', 'JavaScript', 'React'],
                    'experience': '5 ans',
                    'niveau': 'Senior'
                },
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'cors': 'fonctionnel',
                    'origin': 'https://truthtalent.online',
                    'test_mode': True
                }
            }
            
            return {
                'statusCode': 200,
                'headers': response_headers,
                'body': json.dumps(response_body, indent=2)
            }
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'statusCode': 500,
                'headers': response_headers,
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            }
    
    # 7. 404 - ROUTE NON TROUVÉE
    return {
        'statusCode': 404,
        'headers': response_headers,
        'body': json.dumps({
            'error': 'Route non trouvée',
            'path': path,
            'method': http_method,
            'timestamp': datetime.now().isoformat()
        })
    }

# === IMPORTANT: AUCUN CODE EN DEHORS DU HANDLER ===
# Vercel exécute SEULEMENT la fonction handler
# Pas de if __name__ == '__main__' pour la production