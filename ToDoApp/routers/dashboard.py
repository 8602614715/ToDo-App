"""
Dashboard router with role-based access control
"""
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import Annotated, Optional
from urllib.parse import urlencode
from ToDoApp.database import SessionLocal
from ToDoApp.models import ToDoItem, Category, Users
from ToDoApp.routers.auth import get_current_user
from ToDoApp.routers.rbac import require_role, check_role_access, is_admin

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="ToDoApp/template")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# ---------------- DASHBOARD PAGE ----------------


def build_qs(request: Request, exclude: str | None = None) -> str:
    """Build a safe query string excluding one parameter."""
    params = dict(request.query_params)
    if exclude:
        params.pop(exclude, None)
    return urlencode(params)


@router.get("/")
async def dashboard_page(
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
    """Main dashboard page with task list and filters"""
    # Get user info
    db_user = db.query(Users).filter(Users.id == user["user_id"]).first()
    today = date.today()
    
    # Get today's tasks (or recent tasks if none today)
    today_tasks_raw = db.query(ToDoItem).filter(
        ToDoItem.owner_id == user["user_id"]
    ).order_by(ToDoItem.created_at.desc()).limit(4).all()
    
    # Create a list with formatted datetime strings for easier template rendering
    today_tasks = []
    for task in today_tasks_raw:
        # Create a simple object-like structure for the template
        class TaskObj:
            def __init__(self, task):
                self.id = task.id
                self.title = task.title
                self.status = task.status
                if task.created_at:
                    self.created_at_iso = task.created_at.isoformat()
                else:
                    self.created_at_iso = None
                self.created_at = task.created_at  # Keep original for other uses
        today_tasks.append(TaskObj(task))
    
    # Get statistics
    all_todos = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"]).all()
    
    stats = {
        "total": len(all_todos),
        "completed": len([t for t in all_todos if t.status == "completed"]),
        "progress": len([t for t in all_todos if t.status == "progress"]),
        "pending": len([t for t in all_todos if t.status == "pending"]),
        "upcoming": len([t for t in all_todos if t.status == "pending" and t.due_date and t.due_date > today])
    }
    
    # Get project categories (for donut chart and filters)
    categories = db.query(Category).all()
    category_stats = []
    for cat in categories:
        count = len([t for t in all_todos if t.category_id == cat.id])
        if count > 0:
            category_stats.append({
                "name": cat.name,
                "count": count
            })
    
    # Get task analytics data (last 7 days)
    analytics_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_tasks = db.query(ToDoItem).filter(
            and_(
                ToDoItem.owner_id == user["user_id"],
                func.date(ToDoItem.created_at) == day
            )
        ).count()
        analytics_data.append({
            "day": day.strftime("%a"),
            "count": day_tasks
        })
    
    # Get filtered and paginated todos for the task list
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
    
    # Get all for pagination
    all_filtered_todos = query.all()
    
    # Pagination
    total_count = len(all_filtered_todos)
    start = (page - 1) * per_page
    end = start + per_page
    todos = all_filtered_todos[start:end]
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get user's full name
    full_name = f"{db_user.first_name} {db_user.last_name}" if db_user else user.get("username", "User")
    user_title = user.get("user_role", "User").title()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "user_name": full_name,
            "user_title": user_title,
            "today_tasks": today_tasks,
            "stats": stats,
            "category_stats": category_stats,
            "analytics_data": analytics_data,
            "today": today,
            "is_admin": is_admin(user),
            "is_manager": check_role_access(user, ["manager", "admin", "superuser"]),
            "todos": todos,
            "categories": categories,
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
        }
    )


# ---------------- API ENDPOINTS FOR DASHBOARD DATA ----------------


@router.get("/api/analytics")
async def get_analytics(
    db: db_dependency,
    user: user_dependency,
    period: str = "week"  # week, month, year
):
    """Get task analytics data"""
    today = date.today()
    
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:  # year
        days = 365
    
    analytics = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        day_tasks = db.query(ToDoItem).filter(
            and_(
                ToDoItem.owner_id == user["user_id"],
                func.date(ToDoItem.created_at) == day
            )
        ).count()
        analytics.append({
            "date": day.isoformat(),
            "day": day.strftime("%a"),
            "count": day_tasks
        })
    
    return JSONResponse(content={"data": analytics})


@router.get("/api/project-categories")
async def get_project_categories(
    db: db_dependency,
    user: user_dependency
):
    """Get project category statistics"""
    all_todos = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"]).all()
    categories = db.query(Category).all()
    
    category_data = []
    total = len(all_todos)
    
    for cat in categories:
        count = len([t for t in all_todos if t.category_id == cat.id])
        if count > 0:
            percentage = (count / total * 100) if total > 0 else 0
            category_data.append({
                "name": cat.name,
                "count": count,
                "percentage": round(percentage, 1)
            })
    
    return JSONResponse(content={"categories": category_data, "total": total})


@router.get("/api/today-tasks")
async def get_today_tasks(
    db: db_dependency,
    user: user_dependency
):
    """Get today's tasks"""
    today = date.today()
    tasks = db.query(ToDoItem).filter(
        and_(
            ToDoItem.owner_id == user["user_id"],
            func.date(ToDoItem.created_at) == today
        )
    ).order_by(ToDoItem.created_at.desc()).all()
    
    tasks_data = []
    for task in tasks:
        time_ago = "just now"
        if task.created_at:
            delta = datetime.now() - task.created_at
            if delta.seconds < 60:
                time_ago = "just now"
            elif delta.seconds < 3600:
                minutes = delta.seconds // 60
                time_ago = f"{minutes} min ago"
            else:
                hours = delta.seconds // 3600
                time_ago = f"{hours} hour ago"
        
        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "time_ago": time_ago,
            "completed": task.status == "completed"
        })
    
    return JSONResponse(content={"tasks": tasks_data})


@router.get("/api/summary")
async def get_summary(
    db: db_dependency,
    user: user_dependency
):
    """Get summary statistics"""
    all_todos = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"]).all()
    today = date.today()
    
    return JSONResponse(content={
        "total_project": len(all_todos),
        "ongoing_project": len([t for t in all_todos if t.status == "progress"]),
        "upcoming_projects": len([t for t in all_todos if t.status == "pending" and t.due_date and t.due_date > today]),
        "complete_project": len([t for t in all_todos if t.status == "completed"])
    })


@router.get("/api/all-tasks")
async def get_all_tasks(
    db: db_dependency,
    user: user_dependency,
    status: Optional[str] = None
):
    """Get all tasks (with optional status filter) - Role-based access"""
    query = db.query(ToDoItem).filter(ToDoItem.owner_id == user["user_id"])
    
    # Managers and admins can see all tasks, regular users only their own
    if is_admin(user) and status:
        query = query.filter(ToDoItem.status == status)
    
    tasks = query.order_by(ToDoItem.created_at.desc()).all()
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "category": task.category.name if task.category else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat() if task.created_at else None
        })
    
    return JSONResponse(content={"tasks": tasks_data})


@router.post("/api/task/{task_id}/toggle")
async def toggle_task(
    task_id: int,
    db: db_dependency,
    user: user_dependency
):
    """Toggle task completion status"""
    task = db.query(ToDoItem).filter(
        and_(
            ToDoItem.id == task_id,
            ToDoItem.owner_id == user["user_id"]
        )
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == "completed":
        task.status = "pending"
    else:
        task.status = "completed"
    
    db.commit()
    
    return JSONResponse(content={"status": "success", "new_status": task.status})
