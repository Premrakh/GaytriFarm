import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("gaytri_farm_app/firebase-cred.json")
firebase_admin.initialize_app(cred)

