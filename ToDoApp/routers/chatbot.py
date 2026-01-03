from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

class ChatbotRequest(BaseModel):
    message: str

@router.post("/")
async def chatbot(request: ChatbotRequest):
    return {"message": "Hello, I am your To-Do Assistent."}