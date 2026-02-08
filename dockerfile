FROM python:3.11-slim

WORKDIR /app

# Installation minimale
COPY requirements-ultralight.txt .
RUN pip install --no-cache-dir -r requirements-ultralight.txt

# Copie du code
COPY . .

# Port exposé
EXPOSE 10000

# Commande de démarrage
CMD ["python", "app.py"]