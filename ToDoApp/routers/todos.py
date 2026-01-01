from fastapi import APIRouter, Depends, Request, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Annotated
from ToDoApp.database import SessionLocal
from ToDoApp.models import ToDoItem
from ToDoApp.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/todos", tags=["todos"])
templates = Jinja2Templates(directory="ToDoApp/template")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# ---------------- PAGES ----------------
@router.get("/todo-page")
async def todo_page(request: Request, db: db_dependency, user: user_dependency):
    todos = (
        db.query(ToDoItem)
        .filter(ToDoItem.owner_id == user["user_id"])
        .all()
    )

    total = len(todos)
    completed_count = len([t for t in todos if t.status == "completed"])
    todo_count = len([t for t in todos if t.status == "todo"])

    in_progress_count = 0  # only if you actually support this state

    categories = []  # or fetch from DB if you have Category model

    return templates.TemplateResponse(
        "todo.html",
        {
            "request": request,
            "user": user,
            "todos": todos,
            "categories": categories,
            "stats": {
                "total": total,
                "todo": todo_count,
                "in_progress": in_progress_count,
                "completed": completed_count,
            },
        },
    )




@router.get("/add-todo-page")
async def add_todo_page(request: Request, user: user_dependency):
    return templates.TemplateResponse(
        "add-todo.html",
        {"request": request, "user": user}
    )


@router.get("/edit-todo-page/{todo_id}")
async def edit_todo_page(request: Request, todo_id: int, db: db_dependency, user: user_dependency):
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return templates.TemplateResponse(
        "edit-todo.html",
        {"request": request, "todo": todo, "user": user}
    )


# ---------------- FORM ACTIONS ----------------
@router.post("/todo")
async def create_todo(
    db: db_dependency,
    user: user_dependency,
    title: str = Form(...),
    description: str = Form(...),
    priority: int = Form(...)
):
    todo = ToDoItem(
        title=title,
        description=description,
        priority=priority,
        owner_id=user["user_id"]
    )
    db.add(todo)
    db.commit()

    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/todo/{todo_id}/update")
async def update_todo(
    todo_id: int,
    db: db_dependency,
    user: user_dependency,
    title: str = Form(...),
    description: str = Form(...),
    priority: int = Form(...),
    todo_status: str = Form("todo")
):
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todo.title = title
    todo.description = description
    todo.priority = priority
    todo.status = todo_status

    db.commit()

    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/todo/{todo_id}/delete")
async def delete_todo(
    todo_id: int,
    db: db_dependency,
    user: user_dependency
):
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo)
    db.commit()

    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )
