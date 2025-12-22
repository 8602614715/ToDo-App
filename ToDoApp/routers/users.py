from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends, Path
from ToDoApp.models import Users
from ToDoApp import models, schemas
from ToDoApp.database import engine, SessionLocal
from sqlalchemy.orm import Session as session
from ToDoApp.routers import auth
from passlib.context import CryptContext
from passlib.exc import UnknownHashError


router = APIRouter(prefix='/user', tags=['user'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

models.Base.metadata.create_all(bind=engine)

db_dependency = Annotated[session, Depends(get_db)]
user_depedency = Annotated[dict, Depends(auth.get_current_user)]
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



@router.get('/', status_code=200, response_model=schemas.UsersOut)
async def get_user(user: user_depedency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')
    
    db_user = db.query(models.Users).filter(models.Users.id == user.get('user_id')).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    return db_user


@router.put("/password", status_code=204)
async def update_user(db: db_dependency, user: user_depedency, user_verification: schemas.UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    user_db = db.query(models.Users).filter(models.Users.id == user.get('user_id')).first()
    if user_db is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        if not bcrypt_context.verify(user_verification.password, user_db.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect current password")
    except UnknownHashError:
            raise HTTPException(status_code=401, detail="Incorrect current password")


    # Hash and update new password
    hashed_new_password = bcrypt_context.hash(user_verification.new_password)
    user_db.hashed_password = hashed_new_password
    db.add(user_db)
    db.commit()