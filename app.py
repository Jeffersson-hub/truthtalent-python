from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import re
import pdfplumber
import io

app = FastAPI()

# CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"api": "TruthTalent", "status": "ready", "render": True}

@app.get("/health")
def health():
    return {"healthy": True}

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    """Version ultra simple"""
    try:
        # Lire PDF
        contents = await file.read()
        
        # Extraire texte
        text = ""
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        # Regex simple
        email = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        phone = re.findall(r'(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}', text)
        
        return {
            "success": True,
            "email": email[0] if email else None,
            "phone": phone[0] if phone else None,
            "text_preview": text[:200],
            "message": "Render deployment successful"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)