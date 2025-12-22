from fastapi import FastAPI, Request, status
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import models
from database import Engine
from routers import auth, todos, admin, users

app = FastAPI()

# ---------------- SESSION ----------------
app.add_middleware(
    SessionMiddleware,
    secret_key="fb38d7a9ee0761c4769b26c91f408a2392637d24de3959a2113bf7b63987bb7b"
)

# ---------------- DATABASE ----------------
models.Base.metadata.create_all(bind=Engine)

# ---------------- STATIC FILES ----------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- ROUTERS ----------------
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)

# ---------------- TEMPLATES ----------------
templates = Jinja2Templates(directory="template")

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
