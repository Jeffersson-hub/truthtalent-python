#!/bin/bash
echo "🚀 Démarrage TruthTalent API..."

# Mise à jour pip
pip install --upgrade pip

# Installation avec versions compatibles
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    PyPDF2==3.0.1 \
    python-docx==1.1.0 \
    supabase==1.1.1 \
    python-dateutil==2.8.2 \
    "httpx<0.25.0" \
    --no-cache-dir

echo "✅ Installation terminée !"