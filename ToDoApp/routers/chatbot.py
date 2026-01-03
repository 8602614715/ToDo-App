from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ToDoApp.routers.auth import get_current_user
from typing import Annotated

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


@router.post("/chat")
async def chatbot(request: ChatbotRequest, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    reply = rule_based_reply(request.message)
    return {"reply": f"{reply} ({user['username']})"}