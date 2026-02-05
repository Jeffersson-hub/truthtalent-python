# api/index.py - VERSION CORRIGÉE pour Vercel
import sys
import os
from fastapi import FastAPI
from mangum import Mangum  # Important pour Vercel

# Ajouter les chemins
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
lib_dir = os.path.join(root_dir, 'lib')

sys.path.insert(0, lib_dir)
sys.path.insert(0, root_dir)

print(f"📁 Current dir: {current_dir}")
print(f"📁 Root dir: {root_dir}")
print(f"📁 Lib dir: {lib_dir}")

try:
    # Importer l'application principale
    from lib.api.main import app
    print("✅ Application FastAPI importée avec succès")
    
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    
    # Application de secours
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "status": "running",
            "mode": "fallback",
            "error": str(e),
            "check": "Vérifiez que lib/api/main.py existe"
        }
    
    @app.get("/health")
    async def health():
        return {"status": "fallback_mode"}

# Handler pour Vercel (AWS Lambda)
handler = Mangum(app)

# Pour les tests locaux
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)