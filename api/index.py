# api/index.py - VERSION PURE PYTHON
import json
import hashlib
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import os

class APIHandler(BaseHTTPRequestHandler):
    """Handler HTTP pure Python - pas de FastAPI, pas de mangum"""
    
    def do_OPTIONS(self):
        """Gérer les requêtes CORS pre-flight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'https://truthtalent.online')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '3600')
        self.end_headers()
    
    def do_GET(self):
        """Gérer les requêtes GET"""
        if self.path == '/' or self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'https://truthtalent.online')
            self.end_headers()
            
            response = {
                "status": "healthy",
                "service": "TruthTalent API",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Gérer les requêtes POST pour /jobs"""
        try:
            if self.path == '/jobs':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # Simuler un traitement (dans la réalité, vous parseriez le multipart/form-data)
                response_data = {
                    "success": True,
                    "message": "CV reçu (mode test)",
                    "timestamp": datetime.now().isoformat(),
                    "test_mode": True,
                    "note": "API Python pure - fonctionne sans dépendances"
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', 'https://truthtalent.online')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(404)
                self.end_headers()
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', 'https://truthtalent.online')
            self.end_headers()
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(error_response).encode())

def handler(event, context):
    """Handler pour Vercel (AWS Lambda format)"""
    # Cette fonction sera appelée par Vercel
    # Pour simplifier, retournons une réponse basique
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "https://truthtalent.online",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        },
        "body": json.dumps({
            "message": "TruthTalent API (Python)",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        })
    }

# Pour exécution locale
if __name__ == "__main__":
    port = 8000
    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f"✅ Serveur démarré sur http://localhost:{port}")
    server.serve_forever()