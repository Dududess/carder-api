import firebase_admin
from firebase_admin import credentials, firestore
import os

# Charge les credentials Firebase à partir d’un fichier local
cred_path = "app/firebase-adminsdk.json"
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()

def get_user_data(user_id):
    doc = db.collection("users").document(user_id).get()
    if not doc.exists:
        return None
    return doc.to_dict()

def get_user_liked_ads(user_id):
    docs = db.collection("users").document(user_id).collection("liked_ads").stream()
    return [doc.id for doc in docs]

def get_user_disliked_ads(user_id):
    docs = db.collection("users").document(user_id).collection("disliked_ads").stream()
    return [doc.id for doc in docs]


def get_available_car_ads():
    cars_ref = db.collection("car_ads").stream()
    car_list = []

    for car in cars_ref:
        data = car.to_dict()
        data["car_id"] = car.id  # On ajoute l'ID Firebase du document
        data["priceRange"] = price_to_range(data["price"])
        car_list.append(data)

    return car_list

def price_to_range(price: int) -> str:
    # Ex: 15000 → "15k-20k"
    step = 5000
    lower = (price // step) * step
    upper = lower + step
    return f"{lower//1000}k-{upper//1000}k"