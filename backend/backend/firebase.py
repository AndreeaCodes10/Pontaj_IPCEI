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

try:
    import firebase_admin
    from firebase_admin import credentials
except ModuleNotFoundError:
    # Firebase is optional for local/dev. When `firebase_admin` isn't installed,
    # keep this module importable so Django can start (checks/migrations/etc.).
    firebase_admin = None
    credentials = None

FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")

if firebase_admin is None:
    # Firebase not available (dependency not installed)
    pass
elif FIREBASE_KEY_PATH:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred)
else:
    # Firebase disabled (local dev)
    firebase_admin._apps.clear()
