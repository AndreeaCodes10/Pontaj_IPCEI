# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from firebase_admin import auth

# class FirebaseAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         header = request.headers.get("Authorization")

#         if not header:
#             return None

#         token = header.replace("Bearer ", "")

#         try:
#             decoded = auth.verify_id_token(token)
#         except Exception:
#             raise AuthenticationFailed("Invalid Firebase token")

#         user_id = decoded["uid"]

#         return (user_id, None)



from rest_framework.authentication import BaseAuthentication

class DummyAuthentication(BaseAuthentication):
    """
    Dummy auth for local backend testing.
    Always returns a fixed test user.
    """
    def authenticate(self, request):
        return ("testuser", None)
