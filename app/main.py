from fastapi import FastAPI
from app.api import router as api_router
import os
import json
import firebase_admin
from firebase_admin import credentials
from app.ml_utils import load_model_and_mapping

print("🚀 Launching FastAPI app with PORT =", os.environ.get("PORT"))
app = FastAPI(
    title="Carder Recommendation API",
    description="Service de recommandation de voitures basé sur les likes/dislikes utilisateur",
    version="1.0.0",
    debug=True
)
try:
    firebase_key = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    firebase_key_dict = json.loads(firebase_key)
    cred = credentials.Certificate(firebase_key_dict)
    firebase_admin.initialize_app(cred)
    print("Firebase initialized")
except Exception as e:
    print("Firebase init failed:", e)
    
# ✅ Hook de démarrage
@app.on_event("startup")
async def startup_event():
    try:
        print("Chargement du modèle au démarrage...")
        load_model_and_mapping([])
        print("Modèle chargé")
    except Exception as e:
        print(f"Échec du chargement du modèle au démarrage : {e}")
    
app.include_router(api_router)
