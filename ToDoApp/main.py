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
def init_db():
    """Initialize database: create tables and add missing columns"""
    try:
        # Create all tables (for new databases)
        models.Base.metadata.create_all(bind=engine)
        
        # Add missing columns to existing tables (for Render deployments)
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        
        # Check if todo_items table exists and add missing columns
        if inspector.has_table("todo_items"):
            with engine.begin() as conn:
                columns = [col['name'] for col in inspector.get_columns("todo_items")]
                
                if 'status' not in columns:
                    conn.execute(text("ALTER TABLE todo_items ADD COLUMN status VARCHAR(50) DEFAULT 'pending'"))
                    conn.execute(text("ALTER TABLE todo_items ALTER COLUMN status SET NOT NULL"))
                    print("Added 'status' column to todo_items table")
                
                if 'created_at' not in columns:
                    conn.execute(text("ALTER TABLE todo_items ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                    print("Added 'created_at' column to todo_items table")
                
                if 'updated_at' not in columns:
                    conn.execute(text("ALTER TABLE todo_items ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                    print("Added 'updated_at' column to todo_items table")
                
                if 'category_id' not in columns:
                    conn.execute(text("ALTER TABLE todo_items ADD COLUMN category_id INTEGER"))
                    print("Added 'category_id' column to todo_items table")
                
                if 'due_date' not in columns:
                    conn.execute(text("ALTER TABLE todo_items ADD COLUMN due_date DATE"))
                    print("Added 'due_date' column to todo_items table")
                
                if 'tags' not in columns:
                    conn.execute(text("ALTER TABLE todo_items ADD COLUMN tags VARCHAR(255)"))
                    print("Added 'tags' column to todo_items table")
                
                # Update description to TEXT if it's still VARCHAR(255)
                try:
                    conn.execute(text("ALTER TABLE todo_items ALTER COLUMN description TYPE TEXT"))
                    print("Updated 'description' column to TEXT")
                except:
                    pass  # Column might already be TEXT or not exist
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")

init_db()

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
