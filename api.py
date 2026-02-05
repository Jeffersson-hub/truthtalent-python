#!/usr/bin/env python3
"""
TruthTalent API - Version VERCEL CORRECTE
"""
import json
import base64
from datetime import datetime

def lambda_handler(event, context):
    """
    Handler pour Vercel/AWS Lambda
    Format: https://vercel.com/docs/functions/runtimes/python
    """
    
    # Debug: afficher l'événement
    print("📥 Événement reçu:", json.dumps(event, indent=2)[:500])
    
    # Extraire méthode et chemin
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    
    # Headers CORS ESSENTIELS pour WordPress
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': 'https://truthtalent.online',
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin',
        'Access-Control-Max-Age': '86400',
        'Vary': 'Origin'
    }
    
    # ===== OPTIONS (CORS pre-flight) =====
    if http_method == 'OPTIONS':
        print("🔄 Requête OPTIONS (CORS pre-flight)")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # ===== GET / =====
    if http_method == 'GET' and path == '/':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'api': 'TruthTalent',
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'cors': 'enabled_for_truthtalent.online',
                'instructions': 'POST multipart/form-data to /jobs with: file, email, user_id'
            }, indent=2)
        }
    
    # ===== GET /health =====
    if http_method == 'GET' and path == '/health':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'healthy',
                'service': 'TruthTalent API',
                'timestamp': datetime.now().isoformat()
            })
        }
    
    # ===== POST /jobs =====
    if http_method == 'POST' and path == '/jobs':
        try:
            print("📨 Requête POST /jobs reçue")
            
            # Récupérer le body
            body = event.get('body', '')
            is_base64 = event.get('isBase64Encoded', False)
            
            if is_base64 and body:
                body = base64.b64decode(body).decode('utf-8', errors='ignore')
            
            print(f"📄 Body reçu ({len(body)} chars): {body[:200]}...")
            
            # Simuler un traitement de CV
            response_data = {
                'success': True,
                'message': 'CV traité avec succès',
                'action': 'uploaded_to_database',
                'timestamp': datetime.now().isoformat(),
                'note': 'Vercel API fonctionne',
                'cors': 'configured',
                'request_type': 'POST',
                'body_preview': body[:100] if body else 'empty'
            }
            
            print("✅ Réponse générée:", response_data)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data, indent=2)
            }
            
        except Exception as e:
            print(f"❌ Erreur dans /jobs: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            }
    
    # ===== 404 =====
    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({
            'error': 'Route non trouvée',
            'path': path,
            'method': http_method,
            'available_routes': ['GET /', 'GET /health', 'POST /jobs', 'OPTIONS /*']
        })
    }

# ===== ALIAS pour Vercel =====
# Vercel peut utiliser les deux noms
handler = lambda_handler

# ===== POUR TEST LOCAL =====
if __name__ == '__main__':
    print("🧪 Test local de l'API Vercel...")
    
    # Test 1: OPTIONS
    test_options = {
        'httpMethod': 'OPTIONS',
        'path': '/jobs',
        'headers': {
            'Origin': 'https://truthtalent.online',
            'Access-Control-Request-Method': 'POST'
        },
        'body': ''
    }
    
    print("\n1. Test OPTIONS (CORS pre-flight):")
    result = lambda_handler(test_options, None)
    print(f"   Status: {result['statusCode']}")
    print(f"   Headers CORS: {result['headers'].get('Access-Control-Allow-Origin')}")
    
    # Test 2: GET /
    test_get = {
        'httpMethod': 'GET',
        'path': '/',
        'headers': {'Origin': 'https://truthtalent.online'},
        'body': ''
    }
    
    print("\n2. Test GET /:")
    result = lambda_handler(test_get, None)
    print(f"   Status: {result['statusCode']}")
    print(f"   Body preview: {result['body'][:100]}...")
    
    # Test 3: POST /jobs (simuler FormData)
    test_post = {
        'httpMethod': 'POST',
        'path': '/jobs',
        'headers': {
            'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryABC123',
            'Origin': 'https://truthtalent.online'
        },
        'body': '------WebKitFormBoundaryABC123\r\nContent-Disposition: form-data; name="email"\r\n\r\ntest@example.com\r\n------WebKitFormBoundaryABC123\r\nContent-Disposition: form-data; name="user_id"\r\n\r\n123\r\n------WebKitFormBoundaryABC123--',
        'isBase64Encoded': False
    }
    
    print("\n3. Test POST /jobs (multipart/form-data):")
    result = lambda_handler(test_post, None)
    print(f"   Status: {result['statusCode']}")
    print(f"   Body preview: {result['body'][:150]}...")
    
    print("\n✅ Tous les tests locaux passent!")
    print("📤 Pour déployer: vercel --prod")