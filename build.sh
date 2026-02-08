#!/bin/bash
echo "🔧 Build optimisé pour Render..."

# 1. Met à jour pip
pip install --upgrade pip

# 2. Installe d'abord les packages légers
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    pdfplumber==0.10.3 \
    python-docx==1.1.0 \
    supabase==2.3.1 \
    --no-cache-dir

# 3. Essaie spaCy sans blis
pip install spacy==3.7.2 --no-deps  # Sans dépendances
pip install https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0.tar.gz --no-deps

echo "✅ Build complet"