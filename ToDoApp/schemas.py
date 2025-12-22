
from dataclasses import field
from pydantic import BaseModel
from typing import Any
from pydantic import constr


# ---------------- TO-DO ----------------
class ToDoBase(BaseModel):
    title: str = constr(min_length=3)
    description: str = constr(min_length =3, max_length=100)
    priority: int
    complete: bool = False

class ToDoCreate(ToDoBase):
    pass

class ToDoUpdate(ToDoBase):
    pass
    optional_fields: dict[str, Any] = {}

class ToDoOut(ToDoBase):
    id: int

    class Config:
        from_attributes = True


# ---------------- USERS ----------------

class UsersBase(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool = True


# -------------------------------
# For creating a new user
# -------------------------------
class UsersCreate(UsersBase):
    password: str  # only used during registration


# -------------------------------
# For updating user info
# -------------------------------
class UsersUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


# -------------------------------
# For returning data to client (Response model)
# -------------------------------
class UsersOut(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class UserVerification(BaseModel):
    password: str
    new_password: str 