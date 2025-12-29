from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Path
from ToDoApp import models
from ToDoApp.database import engine, SessionLocal
from sqlalchemy.orm import Session as session
from ToDoApp.routers import auth
from ToDoApp.routers.todos import get_db

router = APIRouter(prefix='/admin', tags=['admin'])

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
async def read_all_todos(db: db_dependency, user: user_dependency):
    if not user or user.get('user_role') not in ['admin', 'superuser']:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return db.query(models.ToDoItem).all()

@router.delete("/todo/{todo_id}", status_code=204)
async def delete_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    if not user or user.get('user_role') not in ['admin', 'superuser']:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    todo = db.query(models.ToDoItem).filter(models.ToDoItem.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail='Todo not found.')
    db.delete(todo)
    db.commit()
    return
