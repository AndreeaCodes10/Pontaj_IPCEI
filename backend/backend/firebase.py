# # backend/firebase.py
# import os
# from firebase_admin import credentials, initialize_app

# # Get path to Firebase service account JSON from environment variable
# cred_path = os.getenv("FIREBASE_KEY_PATH")

# if cred_path is None:
#     raise ValueError("FIREBASE_KEY_PATH environment variable not set")

# cred = credentials.Certificate(cred_path)
# initialize_app(cred)

import os
import firebase_admin
from firebase_admin import credentials

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")

if FIREBASE_KEY_PATH:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)
else:
    # Firebase disabled (local dev)
    firebase_admin._apps.clear()
