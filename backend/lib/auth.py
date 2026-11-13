"""MongoDB-backed accounts, JWT authentication, and private analysis history."""
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from bson import ObjectId
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pymongo import MongoClient, DESCENDING

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_TTL_DAYS = 7
security = HTTPBearer(auto_error=False)
_client = None


def get_db():
    global _client
    uri = os.getenv("MONGODB_URI", "")
    if not uri:
        raise HTTPException(503, "Authentication is not configured. Set MONGODB_URI.")
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client[os.getenv("MONGODB_DATABASE", "veritasai")]


def public_user(user):
    return {"id": str(user["_id"]), "fullName": user["fullName"], "email": user["email"]}


def create_token(user_id):
    if not JWT_SECRET:
        raise HTTPException(503, "Authentication is not configured. Set JWT_SECRET.")
    return jwt.encode({"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(days=JWT_TTL_DAYS)}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or not JWT_SECRET:
        raise HTTPException(401, "Please sign in to continue", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])["sub"]
        user = get_db().users.find_one({"_id": ObjectId(user_id)})
    except (JWTError, ValueError):
        user = None
    if not user:
        raise HTTPException(401, "Invalid or expired session", headers={"WWW-Authenticate": "Bearer"})
    return user


def save_history(user_id, text, response, source_type):
    try:
        get_db().search_history.insert_one({
            "user_id": ObjectId(user_id), "input_text": text[:10000],
            "source_type": source_type, "verdict": response.get("overall_verdict"),
            "confidence": response.get("overall_confidence"), "result": response,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        # A history write must not discard a completed verification.
        import logging
        logging.getLogger(__name__).exception("Could not save user search history")


def get_user_history(user_id, limit=50):
    records = get_db().search_history.find({"user_id": ObjectId(user_id)}).sort("created_at", DESCENDING).limit(limit)
    return [{"id": str(r["_id"]), "input_text": r["input_text"], "source_type": r["source_type"],
             "verdict": r.get("verdict"), "confidence": r.get("confidence"),
             "result": r.get("result"), "created_at": r["created_at"].isoformat()} for r in records]
