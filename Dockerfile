# Dockerfile pour API FastAPI + modèle TensorFlow

# Étape 1 : base image légère avec Python
FROM python:3.11-slim

# Étape 2 : définir le répertoire de travail
WORKDIR /app

# Étape 3 : copier les fichiers requirements
COPY requirements.txt .

# Étape 4 : installer les dépendances
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Étape 5 : copier le code de l'application
COPY . .

# Étape 6 : exposer le port 8080 pour Cloud Run
EXPOSE 8080

# Étape 7 : définir la commande de démarrage
# uvicorn doit écouter sur 0.0.0.0:8080 (exigé par Cloud Run)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
