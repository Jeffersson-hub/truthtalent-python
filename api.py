#!/usr/bin/env python3
"""
truthtalent-python.py
Tout dans un seul fichier - 0 dépendances - 0 erreurs VS Code
"""
import json
import hashlib
import sys
from datetime import datetime

print(f"TruthTalent API démarrée avec Python {sys.version}")

def handle_request(method, path, body=""):
    """Gérer une requête HTTP"""
    
    # Headers CORS
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "*"
    }
    
    # Routes
    if method == "OPTIONS":
        return 200, headers, ""
    
    elif method == "GET" and path == "/":
        data = {
            "service": "TruthTalent API",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        return 200, headers, json.dumps(data)
    
    elif method == "POST" and path == "/jobs":
        # Simuler le traitement d'un CV
        data = {
            "success": True,
            "message": "CV reçu avec succès",
            "action": "saved_to_database",
            "timestamp": datetime.now().isoformat()
        }
        return 200, headers, json.dumps(data)
    
    else:
        return 404, headers, json.dumps({"error": "Not found"})

# Pour Vercel
def handler(event, context):
    method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    body = event.get("body", "")
    
    status, headers, body = handle_request(method, path, body)
    
    return {
        "statusCode": status,
        "headers": headers,
        "body": body
    }

# Pour test local
if __name__ == "__main__":
    print("📍 Test local: curl http://localhost:8000/")
    print("📍 Déploiement: vercel --prod")
    
    # Tester
    print("\n🧪 Test interne:")
    status, headers, body = handle_request("GET", "/")
    print(f"GET / -> {status}: {body}")