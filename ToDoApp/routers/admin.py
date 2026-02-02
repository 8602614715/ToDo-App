from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Path, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from ToDoApp import models
from ToDoApp.database import engine, SessionLocal
from sqlalchemy.orm import Session as session
from ToDoApp.routers import auth
from ToDoApp.routers.todos import get_db
from ToDoApp.routers.rbac import require_role, is_admin

router = APIRouter(prefix='/admin', tags=['admin'])
templates = Jinja2Templates(directory="ToDoApp/template")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

models.Base.metadata.create_all(bind=engine)

db_dependency = Annotated[session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth.get_current_user)]

@router.get("/todo", status_code=200)
@require_role(["admin", "superuser"])
async def read_all_todos(db: db_dependency, user: user_dependency):
    """Get all todos - Admin only"""
    return db.query(models.ToDoItem).all()

@router.delete("/todo/{todo_id}", status_code=204)
@require_role(["admin", "superuser"])
async def delete_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    """Delete any todo - Admin only"""
    todo = db.query(models.ToDoItem).filter(models.ToDoItem.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail='Todo not found.')
    db.delete(todo)
    db.commit()
    return

@router.get("/members")
async def members_page(request: Request, db: db_dependency, user: user_dependency):
    """Members management page - Manager and above"""
    if not is_admin(user) and user.get('user_role', '').lower() != 'manager':
        raise HTTPException(status_code=403, detail="Access denied. Manager or Admin role required.")
    
    from ToDoApp.models import Users
    all_users = db.query(Users).all()
    
    return templates.TemplateResponse(
        "admin/members.html",
        {"request": request, "user": user, "users": all_users}
    )
