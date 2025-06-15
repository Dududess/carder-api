import numpy as np
import tensorflow as tf
import os
import joblib
from sklearn.preprocessing import OneHotEncoder
from app.firebase_utils import db, price_to_range
from google.cloud import storage

MODEL_DIR = "app/model"
MODEL_PATH = os.path.join(MODEL_DIR, "model.h5")
_user_encoder = None
_brand_encoder = None
_loaded_model = None

def compute_recommendation_scores(ads: list, preferences: dict, user_id: str, limit: int = 10) -> list:
    load_model_and_mapping(ads)
    predictions = predict_scores(ads, user_id)

    scored_ads = []
    for i, ad in enumerate(ads):
        base_score = predictions[i]
        bonus = 0

        make_pref = preferences.get("make", {})
        year_pref = preferences.get("year", {})
        price_pref = preferences.get("priceRange", {})

        bonus += make_pref.get(ad["brand"], 0) * 0.05
        bonus += year_pref.get(str(ad["year"]), 0) * 0.03
        bonus += price_pref.get(ad["priceRange"], 0) * 0.02

        total_score = base_score + bonus
        ad["score"] = total_score
        ad["source"] = "recommended"
        scored_ads.append(ad)

    return sorted(scored_ads, key=lambda x: x["score"], reverse=True)[:limit]

def train_model():
    users = db.collection("users").stream()
    training_data = []

    for user in users:
        user_id = user.id
        liked_docs = db.collection("users").document(user_id).collection("liked_ads").stream()
        disliked_docs = db.collection("users").document(user_id).collection("disliked_ads").stream()

        for doc in liked_docs:
            ad_ref = db.collection("car_ads").document(doc.id).get()
            if ad_ref.exists:
                ad = ad_ref.to_dict()
                try:
                    training_data.append((user_id, ad["brand"], int(ad["year"]), float(ad["price"]), 1))
                except Exception as e:
                    print(f"[LIKE] Annonce invalide {doc.id} : {e}")

        for doc in disliked_docs:
            ad_ref = db.collection("car_ads").document(doc.id).get()
            if ad_ref.exists:
                ad = ad_ref.to_dict()
                try:
                    training_data.append((user_id, ad["brand"], int(ad["year"]), float(ad["price"]), 0))
                except Exception as e:
                    print(f"[DISLIKE] Annonce invalide {doc.id} : {e}")

    if not training_data:
        print("Aucune donnée d'entraînement.")
        return False

    user_ids = [x[0] for x in training_data]
    brands = [x[1] for x in training_data]
    years = [x[2] for x in training_data]
    prices = [x[3] for x in training_data]
    labels = [x[4] for x in training_data]

    user_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    brand_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

    user_encoded = user_encoder.fit_transform(np.array(user_ids).reshape(-1, 1))
    brand_encoded = brand_encoder.fit_transform(np.array(brands).reshape(-1, 1))

    joblib.dump(user_encoder, os.path.join(MODEL_DIR, "user_encoder.pkl"))
    joblib.dump(brand_encoder, os.path.join(MODEL_DIR, "brand_encoder.pkl"))

    def normalize_year(y): return (y - 2000) / 25
    def normalize_price(p): return p / 100000

    year_scaled = np.array([normalize_year(y) for y in years]).reshape(-1, 1)
    price_scaled = np.array([normalize_price(p) for p in prices]).reshape(-1, 1)

    X = np.hstack([user_encoded, brand_encoded, year_scaled, price_scaled])
    y = np.array(labels)

    print(f"Final input shape : {X.shape}")

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(X.shape[1],)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(X, y, epochs=10, batch_size=16, verbose=1)
    model.save(MODEL_PATH)

    print("✅ Modèle entraîné et sauvegardé")
    return True

def load_model_and_mapping(available_ads):
    global _loaded_model, _user_encoder, _brand_encoder

    if not os.path.exists(MODEL_PATH):
        download_model_files_from_gcs()

    if _loaded_model is None and os.path.exists(MODEL_PATH):
        _loaded_model = tf.keras.models.load_model(MODEL_PATH)

    try:
        _user_encoder = joblib.load(os.path.join(MODEL_DIR, "user_encoder.pkl"))
    except Exception as e:
        print(f"❌ Erreur chargement user_encoder : {e}")

    try:
        _brand_encoder = joblib.load(os.path.join(MODEL_DIR, "brand_encoder.pkl"))
    except Exception as e:
        print(f"❌ Erreur chargement brand_encoder : {e}")

def predict_scores(available_ads, user_id: str):
    if not available_ads or _loaded_model is None or _user_encoder is None or _brand_encoder is None:
        return [0.5] * len(available_ads)

    def normalize_year(y): return (y - 2000) / 25
    def normalize_price(p): return p / 100000

    inputs = []
    for ad in available_ads:
        user_vec = _user_encoder.transform([[user_id]])[0]
        brand_vec = _brand_encoder.transform([[ad["brand"]]])[0]
        year_scaled = normalize_year(ad["year"])
        price_scaled = normalize_price(ad["price"])
        features = list(user_vec) + list(brand_vec) + [year_scaled, price_scaled]
        inputs.append(features)

    inputs_np = np.array(inputs, dtype=np.float32)
    predictions = _loaded_model.predict(inputs_np, verbose=0)
    return predictions.flatten().tolist()

def download_model_files_from_gcs(bucket_name="carder-models", dest_dir=MODEL_DIR):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    for blob_name in ["model.h5", "user_encoder.pkl", "brand_encoder.pkl"]:
        blob = bucket.blob(blob_name)
        local_path = os.path.join(dest_dir, blob_name)
        os.makedirs(dest_dir, exist_ok=True)
        blob.download_to_filename(local_path)
        print(f"✅ Fichier {blob_name} téléchargé depuis GCS")  