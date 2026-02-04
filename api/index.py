import sys
import os

# Ajoutez le dossier lib au chemin Python
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

# Importez votre application depuis lib/api
try:
    from lib.api.main import app  # Ajustez selon votre structure
except ImportError:
    # Fallback si la structure est différente
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"message": "API TruthTalent - Imports à vérifier"}
    
    @app.get("/jobs")
    def jobs():
        return {"error": "Structure lib/ non configurée"}