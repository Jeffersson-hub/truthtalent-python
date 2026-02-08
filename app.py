# app.py - Utilise une API PDF externe GRATUITE
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests  # <-- CELUI-CI MANQUE
import re
import PyPDF2
import io
import os

def extract_pdf_via_external_api(pdf_content: bytes) -> str:
    """Utilise pdftotextonline.com ou similar"""
    
    # Option A: pdftotextonline.com (gratuit, 50 PDF/jour)
    url = "https://pdftotextonline.com/api/extract"
    
    # Option B: CloudConvert (gratuit, 25 conversions/jour)
    # url = "https://api.cloudconvert.com/v2/convert"
    
    # Option C: PDF.co (gratuit, 100 PDF/mois)
    # url = "https://api.pdf.co/v1/pdf/convert/to/text"
    
    files = {'file': ('cv.pdf', pdf_content, 'application/pdf')}
    
    try:
        response = requests.post(url, files=files)
        if response.status_code == 200:
            return response.text
    except:
        pass
    
    return ""

@app.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...)):
    """PDF via service externe"""
    content = await file.read()
    
    # 1. Essaie le service externe
    text = extract_pdf_via_external_api(content)
    
    # 2. Fallback: Base64 pour traitement manuel
    if not text:
        text = f"[PDF base64 - A traiter manuellement]\n{base64.b64encode(content).decode()[:500]}"
    
    return {"text": text[:1000]}