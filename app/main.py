from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(
    title="Carder Recommendation API",
    description="Service de recommandation de voitures basé sur les likes/dislikes utilisateur",
    version="1.0.0",
    debug=True
)

app.include_router(api_router)
