# api/index.py - Optimisé pour Vercel
import sys
import os

# Ajouter le chemin racine et lib au PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
lib_dir = os.path.join(root_dir, 'lib')

sys.path.insert(0, lib_dir)
sys.path.insert(0, root_dir)

print(f"Python path: {sys.path}")
print(f"Current dir: {current_dir}")
print(f"Root dir: {root_dir}")

try:
    # Importer depuis lib/api/main.py
    from lib.api.main import app
    print("✅ Application FastAPI importée avec succès depuis lib/api/main.py")
    
except ImportError as e:
    print(f"❌ Erreur d'importation: {e}")
    print("Tentative d'importation directe...")
    
    # Créer une application de secours
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "status": "running",
            "error": f"Impossible d'importer l'app principale: {str(e)}",
            "check": "Vérifiez que lib/api/main.py existe"
        }
    
    @app.get("/health")
    async def health():
        return {"status": "fallback_mode"}

# Vercel a besoin que l'application s'appelle 'app'
# (déjà le cas puisque nous importons 'app' depuis main.py)