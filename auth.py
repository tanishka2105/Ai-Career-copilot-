import hashlib
import hmac
import os
import time

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException
from google.auth.transport import requests as g_requests
from google.oauth2 import id_token

load_dotenv()
SECRET = os.getenv("JWT_SECRET", "change-me-in-env")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)


def verify(password, salt, stored):
    return hmac.compare_digest(hash_password(password, salt), stored)


def make_token(user_id):
    payload = {"sub": str(user_id), "exp": int(time.time()) + 7 * 24 * 3600}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def current_user(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ").strip()
    try:
        uid = int(jwt.decode(token, SECRET, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Please sign in")
    import db
    if db.get_user_by_id(uid) is None:      # deleted accounts cannot keep using an old token
        raise HTTPException(401, "Please sign in")
    return uid


def verify_google(credential):
    info = id_token.verify_oauth2_token(credential, g_requests.Request(), GOOGLE_CLIENT_ID,
                                        clock_skew_in_seconds=10)
    if not info.get("email_verified"):
        raise ValueError("Google email is not verified")
    return info["email"]