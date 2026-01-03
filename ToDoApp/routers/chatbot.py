from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ToDoApp.routers.auth import get_current_user
from typing import Annotated
from ToDoApp.models import ToDoItem
from ToDoApp.database import SessionLocal

router = APIRouter(prefix="/chatbot", tags=["chatbot"])
user_dependency = Annotated[dict, Depends(get_current_user)]


class ChatbotRequest(BaseModel):
    message: str

def rule_based_reply(message: str) -> str:
    msg = message.lower()
    if "create" in msg and "task" in msg:
        return "Click on 'New Task' to create a task."
    if "edit" in msg:
        return "Click on Edit Button next to a task."
    if "delete" in msg:
        return "Click on Delete Button next to a task."
    if "status" in msg:
        return "Tasks can be pending, Progress, Completed."
    return "I'm sorry, I don't understand your request. Please try again."

def extract_task_title(msg: str) -> str:
    return msg.replace("create task", "").strip()

@router.post("/chat")
async def chatbot(request: ChatbotRequest, user: user_dependency):
    msg = request.message.lower()

    if msg.startswith("create task"):
        title = extract_task_title(msg)
        db = SessionLocal()
        todo = ToDoItem(
            title=title,
            description="created via chatbot",
            priority=3,
            owner_id=user["user_id"],
        )
        db.add(todo)
        db.commit()
        db.close()
        return {"reply": f"Task '{title}' created successfully. ({user['username']})"}
    
    reply = rule_based_reply(request.message)
    return {"reply": f"{reply} ({user['username']})"}