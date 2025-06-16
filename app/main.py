from fastapi import FastAPI
from app.api import router as api_router
import os
import firebase_admin
from firebase_admin import credentials
print("🚀 Launching FastAPI app with PORT =", os.environ.get("PORT"))
app = FastAPI(
    title="Carder Recommendation API",
    description="Service de recommandation de voitures basé sur les likes/dislikes utilisateur",
    version="1.0.0",
    debug=True
)
try:
    cred = credentials.Certificate("/secrets/GOOGLE_APPLICATION_CREDENTIALS")
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized")
except Exception as e:
    print("❌ Firebase init failed:", e)
    
app.include_router(api_router)
