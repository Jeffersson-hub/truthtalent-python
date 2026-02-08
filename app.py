from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import re
import pdfplumber
import io
from docx import Document
from datetime import datetime

app = FastAPI(title="TruthTalent API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change plus tard
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_from_pdf(content: bytes) -> str:
    """Extrait le texte d'un PDF"""
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text

def extract_from_docx(content: bytes) -> str:
    """Extrait le texte d'un DOCX"""
    doc = Document(io.BytesIO(content))
    return "\n".join([para.text for para in doc.paragraphs])

@app.get("/")
def root():
    return {
        "api": "TruthTalent",
        "status": "running",
        "version": "2.0",
        "message": "API déployée sur Render sans spaCy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"healthy": True, "environment": "render-free"}

@app.post("/extract")
async def extract_cv(file: UploadFile = File(...)):
    """Extraction ultra simple - juste email et téléphone"""
    try:
        # Validation
        if not file.filename:
            raise HTTPException(400, "Aucun fichier fourni")
        
        # Lire fichier
        content = await file.read()
        
        # Extraire texte selon format
        text = ""
        if file.filename.lower().endswith('.pdf'):
            text = extract_from_pdf(content)
        elif file.filename.lower().endswith('.docx'):
            text = extract_from_docx(content)
        elif file.filename.lower().endswith('.txt'):
            text = content.decode('utf-8', errors='ignore')
        else:
            raise HTTPException(400, "Format non supporté. Utilisez PDF, DOCX ou TXT")
        
        # Extraction SIMPLE avec regex
        # Email
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        # Téléphone français
        phones = re.findall(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', text)
        # Nom (première ligne avec majuscules)
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
        name = lines[0] if lines else ""
        
        return {
            "success": True,
            "filename": file.filename,
            "extracted": {
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "name": name[:50],
                "email_count": len(emails),
                "phone_count": len(phones)
            },
            "stats": {
                "text_length": len(text),
                "word_count": len(text.split()),
                "line_count": len(text.split('\n'))
            },
            "text_preview": text[:500] + ("..." if len(text) > 500 else ""),
            "timestamp": datetime.now().isoformat(),
            "note": "Version light sans spaCy - Render compatible"
        }
        
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/test")
async def test_upload(file: UploadFile = File(...)):
    """Juste pour tester que l'upload fonctionne"""
    return {
        "received": True,
        "filename": file.filename,
        "size": file.size,
        "content_type": file.content_type
    }

# Port pour Render
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 TruthTalent API démarrée sur le port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)