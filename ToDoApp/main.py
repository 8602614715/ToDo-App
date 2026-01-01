import os
from pathlib import Path
from fastapi import FastAPI, Request, status
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ToDoApp import models
from ToDoApp.database import engine
from ToDoApp.routers import auth, todos, admin, users

app = FastAPI()

# ---------------- SESSION ----------------
app.add_middleware(
    SessionMiddleware,
    secret_key="fb38d7a9ee0761c4769b26c91f408a2392637d24de3959a2113bf7b63987bb7b"
)

# ---------------- DATABASE ----------------
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create database tables: {e}")

# ---------------- STATIC FILES ----------------
# Use absolute path for static files (works on Render)
BASE_DIR = Path(__file__).parent
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ---------------- ROUTERS ----------------
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

# ---------------- TEMPLATES ----------------
# Use absolute path for templates (works on Render)
template_dir = BASE_DIR / "template"
templates = Jinja2Templates(directory=str(template_dir))

# ---------------- ROOT (LANDING PAGE) ----------------
@app.get("/")
async def root(request: Request):
    """
    Public landing page.
    If logged in → dashboard
    Else → landing page (home.html)
    """
    if request.session.get("user"):
        return RedirectResponse(
            url="/todos/todo-page",
            status_code=status.HTTP_302_FOUND
        )

    response = templates.TemplateResponse(
        "home.html",
        {"request": request}
    )
    response.headers["Cache-Control"] = "no-store"
    return response
