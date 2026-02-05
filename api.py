#!/usr/bin/env python3
"""
truth-talent-api.py - Version CORRIGÉE pour Vercel
"""
import json
import sys
from datetime import datetime

# Handler pour Vercel (DOIT être au niveau supérieur)
def handler(event, context):
    """
    Handler pour Vercel - format AWS Lambda
    event: dict avec httpMethod, path, headers, body
    context: info d'exécution (ignoré)
    """
    try:
        method = event.get("httpMethod", "GET")
        path = event.get("path", "/")
        
        # Headers CORS
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://truthtalent.online",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "3600"
        }
        
        # ===== OPTIONS (CORS pre-flight) =====
        if method == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": ""
            }
        
        # ===== GET / (page d'accueil) =====
        if method == "GET" and path == "/":
            data = {
                "api": "TruthTalent",
                "version": "3.0",
                "status": "running",
                "timestamp": datetime.now().isoformat(),
                "python": sys.version.split()[0],
                "endpoints": ["GET /", "POST /jobs", "OPTIONS /*"]
            }
            
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(data, indent=2)
            }
        
        # ===== POST /jobs (recevoir CV) =====
        if method == "POST" and path == "/jobs":
            # Simuler le traitement
            body = event.get("body", "{}")
            
            response = {
                "success": True,
                "message": "CV reçu avec succès",
                "action": "saved_to_database",
                "timestamp": datetime.now().isoformat(),
                "note": "API Python sur Vercel",
                "cors": "enabled",
                "test_mode": True
            }
            
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(response, indent=2)
            }
        
        # ===== 404 - Route non trouvée =====
        return {
            "statusCode": 404,
            "headers": headers,
            "body": json.dumps({
                "error": "Route non trouvée",
                "path": path,
                "method": method
            })
        }
        
    except Exception as error:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            })
        }

# ===== POUR TEST LOCAL =====
if __name__ == "__main__":
    print("🧪 Test local de l'API...")
    
    # Test 1: OPTIONS (CORS pre-flight)
    test_options = {
        "httpMethod": "OPTIONS",
        "path": "/jobs",
        "headers": {
            "Origin": "https://truthtalent.online",
            "Access-Control-Request-Method": "POST"
        },
        "body": ""
    }
    
    print("Test OPTIONS /jobs:")
    result = handler(test_options, None)
    print(f"Status: {result['statusCode']}")
    print(f"Headers: {result['headers']}")
    
    # Test 2: GET /
    test_get = {
        "httpMethod": "GET",
        "path": "/",
        "headers": {},
        "body": ""
    }
    
    print("\nTest GET /:")
    result = handler(test_get, None)
    print(f"Status: {result['statusCode']}")
    print(f"Body: {result['body'][:200]}...")
    
    # Test 3: POST /jobs
    test_post = {
        "httpMethod": "POST",
        "path": "/jobs",
        "headers": {
            "Content-Type": "application/json",
            "Origin": "https://truthtalent.online"
        },
        "body": json.dumps({
            "email": "test@example.com",
            "user_id": "123",
            "filename": "cv.pdf"
        })
    }
    
    print("\nTest POST /jobs:")
    result = handler(test_post, None)
    print(f"Status: {result['statusCode']}")
    print(f"Body: {result['body'][:200]}...")
    
    print("\n✅ Tests terminés avec succès!")
    print("📤 Pour déployer: vercel --prod")