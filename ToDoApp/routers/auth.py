from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Annotated
from ToDoApp.database import SessionLocal
from ToDoApp.models import Users
import ToDoApp.schemas
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from fastapi.templating import Jinja2Templates
from passlib.exc import UnknownHashError

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "fb38d7a9ee0761c4769b26c91f408a2392637d24de3959a2113bf7b63987bb7b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

templates = Jinja2Templates(directory="ToDoApp/template")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


# ---------------- PAGES ----------------
@router.get("/login-page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register-page")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# ---------------- HELPERS ----------------
def authenticate_user(username: str, password: str, db: Session):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    try:
        if bcrypt_context.verify(password, user.hashed_password):
            return user
    except UnknownHashError:
        return False
    return False


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):
    payload = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401)
    return user


# ---------------- AUTH ENDPOINTS ----------------

@router.post("/")
async def create_user(
    db: db_dependency,
    email: str = Form(...),
    username: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    role: str = Form(...),
    password: str = Form(...)
):
    hashed_pw = bcrypt_context.hash(password)

    new_user = Users(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=role,
        hashed_password=hashed_pw,
        is_active=True
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url="/auth/login-page",
        status_code=302
    )



@router.post("/token")
async def login_user(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    request.session["user"] = {
        "username": user.username,
        "user_id": user.id,
        "user_role": user.role
    }

    response = RedirectResponse("/todos/todo-page", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        path="/api"
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)
