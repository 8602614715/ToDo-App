from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import relationship
from ToDoApp.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(150), unique=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50))
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)

    # relationship
    todos = relationship("ToDoItem", back_populates="owner")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    todos = relationship("ToDoItem", back_populates="category")
    
class ToDoItem(Base):
    __tablename__ = "todo_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    description = Column(Text)  # Changed to Text for longer descriptions
    priority = Column(Integer, nullable=False, default=3)  # 1=High, 2=Medium, 3=Low

    # SINGLE source of truth
    status = Column(String(50), default="pending", nullable=False)
    # pending | progress | completed

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # New fields
    due_date = Column(Date, nullable=True)
    tags = Column(String(255), nullable=True)  # Comma-separated tags

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    owner = relationship("Users", back_populates="todos")
    category = relationship("Category", back_populates="todos")
