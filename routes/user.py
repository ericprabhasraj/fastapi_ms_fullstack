import os
import jwt
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from core.db import users_collection
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10))


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    login_message = request.cookies.get("login_message")
    response = templates.TemplateResponse("login.html", {
        "request": request,
        "message": login_message,
        "recaptcha_site_key": RECAPTCHA_SITE_KEY
    })
    response.delete_cookie("login_message")
    return response


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    g_recaptcha_response: str = Form(..., alias="g-recaptcha-response")
):
    data = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": g_recaptcha_response
    }
    async with httpx.AsyncClient() as client:
        r = await client.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        result = r.json()

    if not result.get("success"):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "reCAPTCHA verification failed. Please try again.",
            "recaptcha_site_key": RECAPTCHA_SITE_KEY
        })

    user = users_collection.find_one({"email": email})
    if not user or user["password"] != password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "message": "Invalid email or password.",
            "recaptcha_site_key": RECAPTCHA_SITE_KEY
        })

    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    redirect_url = "/admin-dashboard" if user["role"] == "admin" else "/user-dashboard"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("access_token", access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    response.set_cookie("login_message", "Logged in successfully!", max_age=10)
    return response


@router.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    username: str = Form(...)
):
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "message": "User already exists."
        })

    users_collection.insert_one({
        "email": email,
        "password": password,
        "username": username,
        "role": "user"
    })

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("login_message", "Signup successful! Please log in.", max_age=10)
    return response


@router.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


# ------------------ User Management ------------------

@router.get("/admin/users", response_class=HTMLResponse)
async def get_users(request: Request):
    users = list(users_collection.find())
    print("Fetched Users:", users)  # Debug line

    for user in users:
        user["id"] = str(user["_id"])
        user["username"] = user.get("username", "")
        user["email"] = user.get("email", "")
        user["role"] = user.get("role", "")
    
    return templates.TemplateResponse("user_details.html", {
        "request": request,
        "users": users
    })



@router.get("/admin/users/edit/{user_id}", response_class=HTMLResponse)
async def edit_user_form(request: Request, user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return RedirectResponse("/admin/users", status_code=303)
    user["id"] = str(user["_id"])
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})


@router.post("/admin/users/edit/{user_id}", response_class=HTMLResponse)
async def edit_user(
    request: Request,
    user_id: str,
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form(...)
):
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"username": username, "email": email, "role": role}}
    )
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/users/delete/{user_id}")
async def delete_user(user_id: str):
    users_collection.delete_one({"_id": ObjectId(user_id)})
    return RedirectResponse(url="/admin/users", status_code=303)


# ------------------ shipment Details------------------

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("login_message")
    return response



