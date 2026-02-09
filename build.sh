#!/bin/bash
echo "🚀 Démarrage TruthTalent API optimisé pour Render..."

# Configuration
export PYTHONUNBUFFERED=TRUE
export PYTHONPATH=/opt/render/project/src

# Mise à jour système
apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour pip
pip install --upgrade pip setuptools wheel

# Installation optimisée des dépendances
echo "📦 Installation des dépendances Python..."

pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    PyPDF2==3.0.1 \
    python-docx==1.1.0 \
    supabase==2.3.1 \
    python-dateutil==2.8.2 \
    email-validator==2.1.0 \
    pydantic==2.5.0 \
    --no-cache-dir --no-warn-script-location

# Installation optionnelle de spaCy (pour extraction avancée)
if [ "$INSTALL_SPACY" = "true" ]; then
    echo "📚 Installation de spaCy..."
    pip install spacy==3.7.2 --no-deps
    
    # Téléchargement du modèle français
    wget -q https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0.tar.gz -O /tmp/fr_core_news_sm.tar.gz
    tar -xzf /tmp/fr_core_news_sm.tar.gz -C /tmp
    rm /tmp/fr_core_news_sm.tar.gz
fi

echo "✅ Installation terminée"

# Télécharger le modèle français léger
python -c "
import subprocess
import sys

# Télécharger modèle français sans dépendances
try:
    import urllib.request
    import tarfile
    import os
    
    model_url = 'https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.7.0/fr_core_news_sm-3.7.0.tar.gz'
    model_path = '/tmp/fr_core_news_sm.tar.gz'
    
    print('Téléchargement du modèle français...')
    urllib.request.urlretrieve(model_url, model_path)
    
    print('Extraction du modèle...')
    with tarfile.open(model_path, 'r:gz') as tar:
        tar.extractall('/tmp')
    
    # Installation manuelle
    sys.path.insert(0, '/tmp/fr_core_news_sm-3.7.0')
    
    print('✅ Modèle français téléchargé')
except Exception as e:
    print(f'⚠️ Erreur téléchargement modèle: {e}')
"

# Création du fichier requirements.txt minimal pour Render
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
PyPDF2==3.0.1
python-docx==1.1.0
supabase==2.3.1
python-dateutil==2.8.2
spacy==3.7.2
regex==2023.10.3
EOF

echo "✅ Build terminé avec succès !"