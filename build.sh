#!/bin/bash
echo "🚀 Démarrage TruthTalent API optimisé..."

# Mise à jour pip
pip install --upgrade pip

# Installation minimale sans spaCy
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    PyPDF2==3.0.1 \
    python-docx==1.1.0 \
    supabase==2.3.1 \
    python-dateutil==2.8.2 \
    regex==2023.10.3 \
    pypdf==3.17.4 \
    --no-cache-dir

echo "✅ Installation terminée avec succès !"