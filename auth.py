import hashlib
import hmac
import os
import time

import jwt
from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()
SECRET = os.getenv("JWT_SECRET", "change-me-in-env")


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
        return int(jwt.decode(token, SECRET, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Pehle login karo")