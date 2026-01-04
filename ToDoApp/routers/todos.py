from datetime import date, datetime
from fastapi import APIRouter, Depends, Request, HTTPException, status, Form, Query
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, desc, asc
from typing import Annotated, Optional
from urllib.parse import urlencode
from ToDoApp.database import SessionLocal
from ToDoApp.models import ToDoItem, Category
from ToDoApp.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
import csv
import json

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


# ---------------- HELPER FUNCTIONS ----------------
def get_priority_label(priority: int) -> str:
    """Convert priority number to label"""
    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    return priority_map.get(priority, "Low")

def is_overdue(due_date) -> bool:
    """Check if a task is overdue"""
    if not due_date:
        return False
    return due_date < date.today()

def parse_tags(tags_str: Optional[str]) -> list:
    """Parse comma-separated tags string into list"""
    if not tags_str:
        return []
    return [tag.strip() for tag in tags_str.split(",") if tag.strip()]

def build_qs(request: Request, exclude: str | None = None) -> str:
    """
    Build a safe query string excluding one parameter.
    """
    params = dict(request.query_params)
    if exclude:
        params.pop(exclude, None)
    return urlencode(params)

# ---------------- PAGES ----------------
@router.get("/todo-page")
async def todo_page(
    request: Request,
    db: db_dependency,
    user: user_dependency,
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    category_id: Optional[int] = Query(None),
    priority_filter: Optional[int] = Query(None, alias="priority"),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Main todo page with search, filter, and sort"""
    # Base query
    query = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"])
    
    # Search functionality
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ToDoItem.title.ilike(search_term),
                ToDoItem.description.ilike(search_term),
                ToDoItem.tags.ilike(search_term)
            )
        )
    
    # Status filter
    if status_filter:
        query = query.filter(ToDoItem.status == status_filter)
    
    # Category filter
    if category_id:
        query = query.filter(ToDoItem.category_id == category_id)
    
    # Priority filter
    if priority_filter:
        query = query.filter(ToDoItem.priority == priority_filter)
    
    # Sorting
    sort_column = {
        "title": ToDoItem.title,
        "priority": ToDoItem.priority,
        "status": ToDoItem.status,
        "due_date": ToDoItem.due_date,
        "created_at": ToDoItem.created_at,
        "updated_at": ToDoItem.updated_at
    }.get(sort_by, ToDoItem.created_at)
    
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))
    
    # Get all for stats
    all_todos = query.all()
    
    # Pagination
    total_count = len(all_todos)
    start = (page - 1) * per_page
    end = start + per_page
    todos = all_todos[start:end]
    
    # Calculate stats
    all_user_todos = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"]).all()
    total = len(all_user_todos)
    completed_count = len([t for t in all_user_todos if t.status == "completed"])
    pending_count = len([t for t in all_user_todos if t.status == "pending"])
    progress_count = len([t for t in all_user_todos if t.status == "progress"])
    
    # Get categories
    categories = db.query(Category).all()
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    
    qs_no_category = build_qs(request, "category_id")
    qs_no_status = build_qs(request, "status")
    qs_no_priority = build_qs(request, "priority")
  
 
    return templates.TemplateResponse(
        "todo.html",
        {
            "request": request,
            "user": user,
            "todos": todos,
            "categories": categories,
            "today": date.today(),
            "stats": {
                "total": total,
                "pending": pending_count,
                "progress": progress_count,
                "completed": completed_count,
            },
            "filters": {
                "search": search or "",
                "status": status_filter,
                "category_id": category_id,
                "priority": priority_filter,
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_count": total_count,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
        "qs_no_category": qs_no_category,
        "qs_no_status": qs_no_status,
        "qs_no_priority": qs_no_priority,
        },
    )


@router.get("/add-todo-page")
async def add_todo_page(request: Request, db: db_dependency, user: user_dependency):
    """Add new todo page"""
    categories = db.query(Category).all()
    return templates.TemplateResponse(
        "add-todo.html",
        {"request": request, "user": user, "categories": categories, "today": date.today()}
    )


@router.get("/edit-todo-page/{todo_id}")
async def edit_todo_page(request: Request, todo_id: int, db: db_dependency, user: user_dependency):
    """Edit todo page"""
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    categories = db.query(Category).all()

    return templates.TemplateResponse(
        "edit-todo.html",
        {"request": request, "todo": todo, "user": user, "categories": categories}
    )


@router.get("/todo-details/{todo_id}")
async def todo_details_page(request: Request, todo_id: int, db: db_dependency, user: user_dependency):
    """Detailed view of a single todo"""
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    return templates.TemplateResponse(
        "todo-details.html",
        {"request": request, "todo": todo, "user": user, "today": date.today()}
    )


# ---------------- FORM ACTIONS ----------------
@router.post("/todo")
async def create_todo(
    db: db_dependency,
    user: user_dependency,
    title: str = Form(...),
    description: str = Form(""),
    priority: int = Form(3),
    category_id: Optional[int] = Form(None),
    due_date: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """Create a new todo"""
    todo = ToDoItem(
        title=title,
        description=description,
        priority=priority,
        owner_id=user["user_id"],
        category_id=category_id if category_id else None,
        tags=tags if tags else None
    )
    
    if due_date:
        try:
            todo.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except:
            pass  # Invalid date format, skip
    
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
    description: str = Form(""),
    priority: int = Form(3),
    todo_status: str = Form("pending"),
    category_id: Optional[int] = Form(None),
    due_date: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """Update an existing todo"""
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
    todo.category_id = category_id if category_id else None
    todo.tags = tags if tags else None
    
    if due_date:
        try:
            todo.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except:
            todo.due_date = None
    else:
        todo.due_date = None

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
    """Delete a todo"""
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


# ---------------- QUICK ACTIONS ----------------
@router.post("/todo/{todo_id}/quick-status")
async def quick_status_change(
    todo_id: int,
    db: db_dependency,
    user: user_dependency,
    new_status: str = Form(...)
):
    """Quick status change without full edit"""
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if new_status in ["pending", "progress", "completed"]:
        todo.status = new_status
        db.commit()

    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/todo/{todo_id}/toggle-complete")
async def toggle_complete(
    todo_id: int,
    db: db_dependency,
    user: user_dependency
):
    """Toggle todo completion status"""
    todo = db.query(ToDoItem)\
        .filter(ToDoItem.id == todo_id)\
        .filter(ToDoItem.owner_id == user["user_id"])\
        .first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if todo.status == "completed":
        todo.status = "pending"
    else:
        todo.status = "completed"
    
    db.commit()

    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )


# ---------------- EXPORT FUNCTIONALITY ----------------
@router.get("/export")
async def export_todos(
    db: db_dependency,
    user: user_dependency,
    format: str = Query("csv", regex="^(csv|json)$")
):
    """Export todos to CSV or JSON"""
    todos = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"]).all()
    
    if format == "csv":
        output = []
        output.append(["ID", "Title", "Description", "Status", "Priority", "Category", "Due Date", "Tags", "Created At"])
        
        for todo in todos:
            output.append([
                todo.id,
                todo.title,
                todo.description or "",
                todo.status,
                get_priority_label(todo.priority),
                todo.category.name if todo.category else "",
                todo.due_date.strftime("%Y-%m-%d") if todo.due_date else "",
                todo.tags or "",
                todo.created_at.strftime("%Y-%m-%d %H:%M:%S") if todo.created_at else ""
            ])
        
        csv_content = "\n".join([",".join([str(cell) for cell in row]) for row in output])
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=todos_{date.today()}.csv"}
        )
    
    else:  # JSON
        todos_data = []
        for todo in todos:
            todos_data.append({
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "status": todo.status,
                "priority": get_priority_label(todo.priority),
                "priority_value": todo.priority,
                "category": todo.category.name if todo.category else None,
                "due_date": todo.due_date.isoformat() if todo.due_date else None,
                "tags": parse_tags(todo.tags),
                "created_at": todo.created_at.isoformat() if todo.created_at else None,
                "updated_at": todo.updated_at.isoformat() if todo.updated_at else None
            })
        
        return Response(
            content=json.dumps(todos_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=todos_{date.today()}.json"}
        )


# ---------------- CATEGORY MANAGEMENT ----------------
@router.post("/category")
async def create_category(
    db: db_dependency,
    user: user_dependency,
    name: str = Form(...)
):
    """Create a new category"""
    # Check if category already exists
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = Category(name=name)
    db.add(category)
    db.commit()
    
    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/category/{category_id}/delete")
async def delete_category(
    category_id: int,
    db: db_dependency,
    user: user_dependency
):
    """Delete a category"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Remove category from todos
    db.query(ToDoItem).filter(ToDoItem.category_id == category_id).update({"category_id": None})
    
    db.delete(category)
    db.commit()
    
    return RedirectResponse(
        url="/todos/todo-page",
        status_code=status.HTTP_302_FOUND
    )
