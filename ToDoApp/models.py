import datetime
from sqlalchemy.types import DateTime
from ToDoApp.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(150), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50))
    hashed_password = Column(String(255))  # ✅ store hashed password here
    is_active = Column(Boolean, default=True)
    
class ToDoItem(Base):
    __tablename__ ="todo_items"

    id = Column (Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    description = Column(String(255))
    priority = Column(Integer, nullable=False)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50), default="todo")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    category_id = Column(Integer, ForeignKey("categories.id"))
    



