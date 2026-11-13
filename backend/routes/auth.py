"""Account endpoints for JWT sign-in and private search history."""
import re
import bcrypt
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from lib.auth import create_token, current_user, get_db, get_user_history, public_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignUp(BaseModel):
    fullName: str
    email: EmailStr
    password: str


class Login(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", status_code=201)
def signup(data: SignUp):
    name = data.fullName.strip()
    if not name or len(data.password) < 6:
        raise HTTPException(400, "Enter your name and a password of at least 6 characters")
    db = get_db()
    email = str(data.email).lower()
    if db.users.find_one({"email": email}):
        raise HTTPException(409, "An account with this email already exists")
    user = {"fullName": name, "email": email, "password": bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()}
    result = db.users.insert_one(user)
    user["_id"] = result.inserted_id
    return {"token": create_token(result.inserted_id), "user": public_user(user)}


@router.post("/login")
def login(data: Login):
    user = get_db().users.find_one({"email": str(data.email).lower()})
    if not user or not bcrypt.checkpw(data.password.encode(), user["password"].encode()):
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_token(user["_id"]), "user": public_user(user)}


@router.get("/me")
def me(user=Depends(current_user)):
    return public_user(user)


@router.get("/history")
def history(limit: int = 50, user=Depends(current_user)):
    return {"data": get_user_history(user["_id"], min(max(limit, 1), 100))}
