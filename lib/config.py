import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Render
    PORT = int(os.getenv("PORT", 10000))
    HOST = "0.0.0.0"
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # Frontend
    FRONTEND_URL = os.getenv("ALLOWED_ORIGINS", "https://truthtalent.online").split(",")[0]
    
    # API
    API_URL = os.getenv("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")
    
    @classmethod
    def validate(cls):
        """Valide la configuration"""
        errors = []
        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL manquant")
        if not cls.SUPABASE_KEY:
            errors.append("SUPABASE_KEY manquant")
        return errors