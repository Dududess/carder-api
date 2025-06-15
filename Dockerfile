# Dockerfile pour API FastAPI + modèle TensorFlow

# 1. Base image officielle Python
FROM python:3.12-slim

# 2. Dossier de travail
WORKDIR /app

# 3. Copie des fichiers de l'application
COPY . /app

# 4. Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 5. Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 6. Port exposé par Uvicorn
EXPOSE 8080

# 7. Commande de lancement (serveur ASGI avec hot reload désactivé)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
