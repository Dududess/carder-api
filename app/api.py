from fastapi import APIRouter, Query
from app.firebase_utils import get_user_data, get_available_car_ads, get_user_disliked_ads, get_user_liked_ads
from app.ml_utils import compute_recommendation_scores, train_model, _loaded_model
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, limit: int = Query(default=10, ge=1, le=50)):
    user_data = get_user_data(user_id)
    if not user_data:
        return {"error": "Utilisateur inconnu"}

    liked_ids = get_user_liked_ads(user_id)
    disliked_ids = get_user_disliked_ads(user_id)
    preferences = user_data.get("preferences", {})

    all_ads = get_available_car_ads()
    ads_to_recommend = [
        ad for ad in all_ads
        if ad["car_id"] not in liked_ids and ad["car_id"] not in disliked_ids
    ]
    preferences["user_id"] = user_id

    scored_ads = compute_recommendation_scores(ads_to_recommend, preferences, user_id, limit)
    return {"recommended_ads": scored_ads}


@router.post("/train_model")
async def trigger_model_training():
    success = train_model()
    if success:
        return {"message": "Modèle entraîné avec succès."}
    return JSONResponse(status_code=500, content={"error": "Échec de l'entraînement du modèle."})


@router.get("/status")
async def model_status():
    if _loaded_model:
        return {"status": "loaded"}
    return {"status": "not loaded"}
