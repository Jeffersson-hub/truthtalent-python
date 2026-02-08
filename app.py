#!/usr/bin/env python3
"""
TruthTalent API - Version RENDER CORRECTE
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import re
import io

# ========== D'ABORD, CRÉER 'app' ==========
app = FastAPI(title="TruthTalent API")

# ========== ENSUITE, MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MAINTENANT LES ROUTES ==========
@app.get("/")
def home():
    return {
        "api": "TruthTalent",
        "status": "running",
        "environment": "Render",
        "version": "1.0"
    }

@app.get("/health")
def health():
    return {"healthy": True, "service": "TruthTalent API"}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    """Extrait les infos d'un CV (PDF ou TXT)"""
    try:
        # Validation
        if not file.filename:
            raise HTTPException(400, "Nom de fichier manquant")
        
        # Lire le fichier
        content = await file.read()
        
        # Détecter le type
        is_pdf = file.filename.lower().endswith('.pdf')
        
        # Extraire le texte (version simplifiée)
        text = ""
        if is_pdf:
            # Pour PDF - version simple (à améliorer)
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            except ImportError:
                text = "[PDF - nécessite PyPDF2]"
                pass
        else:
            # Pour TXT
            text = content.decode('utf-8', errors='ignore')
        
        # Extraction email
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        
        # Extraction téléphone français
        phones = re.findall(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', text)
        
        # Nom potentiel (première ligne non vide)
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
        name = lines[0] if lines else ""
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted": {
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "name": name[:100],
                "email_count": len(emails),
                "phone_count": len(phones)
            },
            "text_preview": text[:500] + ("..." if len(text) > 500 else ""),
            "format": "pdf" if is_pdf else "txt"
        }
        
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Juste pour tester que l'upload fonctionne"""
    return {
        "received": True,
        "filename": file.filename,
        "size": file.size,
        "content_type": file.content_type
    }

# ========== POINT D'ENTRÉE POUR RENDER ==========
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 TruthTalent API démarrée sur le port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)