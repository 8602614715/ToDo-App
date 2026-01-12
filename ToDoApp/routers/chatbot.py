import re
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Annotated, Optional
from ToDoApp.routers.auth import get_current_user
from ToDoApp.models import ToDoItem, Category
from ToDoApp.database import SessionLocal

router = APIRouter(prefix="/chatbot", tags=["chatbot"])
user_dependency = Annotated[dict, Depends(get_current_user)]


class ChatbotRequest(BaseModel):
    message: str


class ChatbotResponse(BaseModel):
    reply: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


# ---------------- NATURAL LANGUAGE PROCESSING ----------------


def extract_intent(message: str) -> str:
    msg = message.lower().strip()

    if any(w in msg for w in ["create", "add", "new", "make"]) and "task" in msg:
        return "create"

    if any(w in msg for w in ["update", "edit", "change", "modify"]) and "task" in msg:
        return "update"

    if any(w in msg for w in ["delete", "remove"]) and "task" in msg:
        return "delete"

    if any(w in msg for w in ["list", "show", "display", "my tasks"]):
        return "list"

    if any(w in msg for w in ["status", "progress", "statistics"]):
        return "status"

    if any(w in msg for w in ["help", "commands"]):
        return "help"

    if any(w in msg for w in ["hi", "hello", "hey"]):
        return "greeting"

    return "unknown"

   


def extract_task_id(message: str):
    patterns = [
        r'task\s*(?:#|id|number)?\s*(\d{1,3})',
        r'#(\d{1,3})'
    ]

    for p in patterns:
        m = re.search(p, message.lower())
        if m:
            return int(m.group(1))
    return None



def extract_title(message: str, intent: str) -> Optional[str]:
    """Extract task title from message"""
    msg = message.strip()
    
    # Remove intent keywords
    remove_patterns = [
        r'^(create|add|new|make)\s+(?:a\s+)?(?:new\s+)?(?:task|todo|item)[\s:]*',
        r'^(update|edit|change|modify)\s+(?:task|todo|item)\s*(?:#|number|id)?\s*\d*[\s:]*',
        r'^(delete|remove|drop)\s+(?:task|todo|item)\s*(?:#|number|id)?\s*\d*[\s:]*',
    ]
    
    for pattern in remove_patterns:
        msg = re.sub(pattern, '', msg, flags=re.IGNORECASE)
    
    # Extract text in quotes
    quoted = re.search(r'["\']([^"\']+)["\']', msg)
    if quoted:
        return quoted.group(1).strip()
    
    # Extract text after colon
    if ':' in msg:
        parts = msg.split(':', 1)
        if len(parts) > 1:
            title = parts[1].strip()
            # Remove description if present
            if 'description' in title.lower() or 'desc' in title.lower():
                title = re.sub(r'description[:\s]*.*', '', title, flags=re.IGNORECASE)
            return title.split(',')[0].strip() if title else None
    
    # Extract first meaningful phrase
    words = msg.split()
    if len(words) > 0:
        # Take first 5-10 words as title
        title = ' '.join(words[:10])
        # Remove common words
        title = re.sub(r'\b(with|priority|status|description|desc)\b.*', '', title, flags=re.IGNORECASE)
        return title.strip() if title.strip() else None
    
    return None


def extract_description(message: str) -> Optional[str]:
    """Extract description from message"""
    # Look for "description:", "desc:", or text after comma
    patterns = [
        r'description[:\s]+([^,]+)',
        r'desc[:\s]+([^,]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # If message has comma, description might be after it
    if ',' in message:
        parts = message.split(',', 1)
        if len(parts) > 1:
            desc = parts[1].strip()
            # Remove priority/status keywords
            desc = re.sub(r'\b(priority|status|high|medium|low|pending|progress|completed)\b.*', '', desc, flags=re.IGNORECASE)
            return desc.strip() if desc.strip() else None
    
    return None


def extract_priority(message: str) -> int:
    """Extract priority from message (default: 3 = Low)"""
    msg = message.lower()
    
    # Check for explicit priority numbers
    if re.search(r'priority\s*(?:is\s*)?(?:=)?\s*([123])', msg):
        match = re.search(r'priority\s*(?:is\s*)?(?:=)?\s*([123])', msg)
        return int(match.group(1))
    
    # Check for priority words
    if any(word in msg for word in ["high priority", "priority high", "important", "urgent"]):
        return 1
    if any(word in msg for word in ["medium priority", "priority medium", "normal"]):
        return 2
    if any(word in msg for word in ["low priority", "priority low", "not important"]):
        return 3
    
    return 3  # Default to low


def extract_status(message: str) -> Optional[str]:
    """Extract status from message"""
    msg = message.lower()
    
    if any(word in msg for word in ["completed", "complete", "done", "finished"]):
        return "completed"
    if any(word in msg for word in ["progress", "in progress", "working", "started"]):
        return "progress"
    if any(word in msg for word in ["pending", "not started", "todo"]):
        return "pending"
    
    return None


def extract_category_name(message: str, db: Session) -> Optional[int]:
    """Extract category ID from message by matching category name"""
    msg = message.lower()
    
    # Get all categories
    categories = db.query(Category).all()
    
    # Check if any category name appears in the message
    for category in categories:
        if category.name.lower() in msg:
            return category.id
    
    return None


def extract_filters(message: str, db: Session) -> dict:
    """Extract all filter parameters from message"""
    filters = {
        "priority": None,
        "status": None,
        "category_id": None
    }
    
    # Extract priority filter
    msg_lower = message.lower()
    if any(word in msg_lower for word in ["high priority", "priority high", "high"]):
        filters["priority"] = 1
    elif any(word in msg_lower for word in ["medium priority", "priority medium", "medium"]):
        filters["priority"] = 2
    elif any(word in msg_lower for word in ["low priority", "priority low", "low"]):
        filters["priority"] = 3
    
    # Extract status filter
    status = extract_status(message)
    if status:
        filters["status"] = status
    
    # Extract category filter
    category_id = extract_category_name(message, db)
    if category_id:
        filters["category_id"] = category_id
    
    return filters


def get_priority_label(priority: int) -> str:
    """Convert priority number to label"""
    priority_map = {1: "High", 2: "Medium", 3: "Low"}
    return priority_map.get(priority, "Low")


# ---------------- CHATBOT HANDLERS ----------------


def handle_greeting() -> str:
    return "Hello! I'm your task assistant. I can help you:\n" \
           "• Create tasks\n" \
           "• Update/edit tasks\n" \
           "• Delete tasks\n" \
           "• List all your tasks\n" \
           "• Check task status and statistics\n\n" \
           "Try saying: 'Create task: Buy groceries' or 'Show all my tasks'"


def handle_help() -> str:
    return """Here's what I can do:

**Create a task:**
- "Create task: [title]"
- "Add task: [title] with description [description]"
- "New task: [title], priority high"

**Update a task:**
- "Update task #1: [new title]"
- "Edit task 2, status completed"
- "Change task #3, priority high"

**Delete a task:**
- "Delete task #1"
- "Remove task 2"

**List tasks (with filters):**
- "Show all tasks"
- "List my tasks"
- "Show tasks with high priority"
- "List pending tasks"
- "Show tasks in [category name]"
- "Display completed tasks"
- "Show tasks with medium priority and status progress"

**Check status:**
- "What's my task status?"
- "Show statistics"
- "How many tasks do I have?"

You can filter tasks by priority (high/medium/low), status (pending/progress/completed), and category name when listing tasks."""


def handle_create(message: str, db: Session, user_id: int) -> str:
    """Handle task creation"""
    title = extract_title(message, "create")
    if not title:
        return "I couldn't find a task title. Please try: 'Create task: [your task title]'"
    
    description = extract_description(message) or "Created via chatbot"
    priority = extract_priority(message)
    status = extract_status(message) or "pending"
    
    # Create the task
    todo = ToDoItem(
        title=title,
        description=description,
        priority=priority,
        status=status,
        owner_id=user_id
    )
    
    db.add(todo)
    db.commit()
    db.refresh(todo)
    
    return f"✅ Task created successfully!\n" \
           f"**ID:** {todo.id}\n" \
           f"**Title:** {todo.title}\n" \
           f"**Description:** {todo.description}\n" \
           f"**Priority:** {get_priority_label(todo.priority)}\n" \
           f"**Status:** {todo.status}"


def handle_update(message: str, db: Session, user_id: int) -> str:
    """Handle task update"""
    task_id = extract_task_id(message)
    if not task_id:
        return "I couldn't find a task ID. Please specify which task to update, e.g., 'Update task #1: [new title]'"
    
    # Find the task
    todo = db.query(ToDoItem).filter(
        ToDoItem.id == task_id,
        ToDoItem.owner_id == user_id
    ).first()
    
    if not todo:
        return f"❌ Task #{task_id} not found. Please check the task ID."
    
    # Extract updates
    title = extract_title(message, "update")
    description = extract_description(message)
    priority = extract_priority(message)
    status = extract_status(message)
    
    # Apply updates
    updates = []
    if title and title != todo.title:
        todo.title = title
        updates.append(f"Title: {title}")
    
    if description:
        todo.description = description
        updates.append(f"Description: {description}")
    
    if priority != todo.priority:
        todo.priority = priority
        updates.append(f"Priority: {get_priority_label(priority)}")
    
    if status and status != todo.status:
        todo.status = status
        updates.append(f"Status: {status}")
    
    if not updates:
        return f"Task #{task_id} found, but no changes detected. Please specify what to update."
    
    todo.updated_at = datetime.utcnow()
    db.commit()
    
    return f"✅ Task #{task_id} updated successfully!\n" + "\n".join([f"• {u}" for u in updates])


def handle_delete(message: str, db: Session, user_id: int) -> str:
    """Handle task deletion"""
    task_id = extract_task_id(message)
    if not task_id:
        return "I couldn't find a task ID. Please specify which task to delete, e.g., 'Delete task #1'"
    
    # Find the task
    todo = db.query(ToDoItem).filter(
        ToDoItem.id == task_id,
        ToDoItem.owner_id == user_id
    ).first()
    
    if not todo:
        return f"❌ Task #{task_id} not found. Please check the task ID."
    
    title = todo.title
    db.delete(todo)
    db.commit()
    
    return f"✅ Task #{task_id} '{title}' deleted successfully!"


def handle_list(message: str, db: Session, user_id: int) -> str:
    """Handle listing all tasks with optional filters"""
    # Extract filters from message
    filters = extract_filters(message, db)
    
    # Build query with filters
    query = db.query(ToDoItem).filter(ToDoItem.owner_id == user_id)
    
    # Apply priority filter
    if filters["priority"]:
        query = query.filter(ToDoItem.priority == filters["priority"])
    
    # Apply status filter
    if filters["status"]:
        query = query.filter(ToDoItem.status == filters["status"])
    
    # Apply category filter
    if filters["category_id"]:
        query = query.filter(ToDoItem.category_id == filters["category_id"])
    
    # Get filtered results
    todos = query.order_by(ToDoItem.created_at.desc()).all()
    
    if not todos:
        filter_info = []
        if filters["priority"]:
            filter_info.append(f"priority {get_priority_label(filters['priority'])}")
        if filters["status"]:
            filter_info.append(f"status {filters['status']}")
        if filters["category_id"]:
            category = db.query(Category).filter(Category.id == filters["category_id"]).first()
            if category:
                filter_info.append(f"category '{category.name}'")
        
        if filter_info:
            return f"📝 No tasks found with filters: {', '.join(filter_info)}.\nTry removing filters or create a new task."
        return "📝 You don't have any tasks yet. Create one by saying 'Create task: [your task]'"
    
    # Build filter description
    filter_desc = []
    if filters["priority"]:
        filter_desc.append(f"Priority: {get_priority_label(filters['priority'])}")
    if filters["status"]:
        filter_desc.append(f"Status: {filters['status']}")
    if filters["category_id"]:
        category = db.query(Category).filter(Category.id == filters["category_id"]).first()
        if category:
            filter_desc.append(f"Category: {category.name}")
    
    filter_text = f" (filtered: {', '.join(filter_desc)})" if filter_desc else ""
    response = f"📋 **Your Tasks ({len(todos)} total{filter_text}):**\n\n"
    
    for todo in todos:
        status_emoji = {
            "completed": "✅",
            "progress": "🔄",
            "pending": "⏳"
        }.get(todo.status, "⏳")
        
        priority_emoji = {
            1: "🔴",
            2: "🟡",
            3: "🟢"
        }.get(todo.priority, "🟢")
        
        category_text = f" | Category: {todo.category.name}" if todo.category else ""
        
        response += f"{status_emoji} **#{todo.id}** {priority_emoji} {todo.title}\n"
        response += f"   Status: {todo.status} | Priority: {get_priority_label(todo.priority)}{category_text}\n"
        if todo.description:
            desc = todo.description[:50] + "..." if len(todo.description) > 50 else todo.description
            response += f"   {desc}\n"
        response += "\n"
    
    return response


def handle_status(db: Session, user_id: int) -> str:
    """Handle status query"""
    todos = db.query(ToDoItem).filter(ToDoItem.owner_id == user_id).all()
    
    if not todos:
        return "📊 You don't have any tasks yet."
    
    total = len(todos)
    completed = len([t for t in todos if t.status == "completed"])
    progress = len([t for t in todos if t.status == "progress"])
    pending = len([t for t in todos if t.status == "pending"])
    
    high_priority = len([t for t in todos if t.priority == 1])
    medium_priority = len([t for t in todos if t.priority == 2])
    low_priority = len([t for t in todos if t.priority == 3])
    
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    response = f"📊 **Task Statistics:**\n\n"
    response += f"**Total Tasks:** {total}\n\n"
    response += f"**By Status:**\n"
    response += f"✅ Completed: {completed}\n"
    response += f"🔄 In Progress: {progress}\n"
    response += f"⏳ Pending: {pending}\n\n"
    response += f"**By Priority:**\n"
    response += f"🔴 High: {high_priority}\n"
    response += f"🟡 Medium: {medium_priority}\n"
    response += f"🟢 Low: {low_priority}\n\n"
    response += f"**Completion Rate:** {completion_rate:.1f}%"
    
    return response


def handle_unknown(message: str) -> str:
    return "I'm sorry, I don't understand that request. Here's what I can help you with:\n\n" \
           "• Create tasks: 'Create task: [title]'\n" \
           "• Update tasks: 'Update task #1: [changes]'\n" \
           "• Delete tasks: 'Delete task #1'\n" \
           "• List tasks: 'Show all tasks'\n" \
           "• Check status: 'What's my task status?'\n\n" \
           "Type 'help' for more information."


# ---------------- MAIN CHATBOT ENDPOINT ----------------


@router.post("/chat", response_model=ChatbotResponse)
async def chatbot(
    request: ChatbotRequest,
    user: user_dependency,
    db: db_dependency
):
    raw_message = request.message.strip()
    if not raw_message:
        return ChatbotResponse(reply="Please type a message.")

    # ✅ AI NORMALIZATION (NEW)
    message = normalize_with_ai(raw_message)

    intent = extract_intent(message)
    user_id = user["user_id"]
    username = user.get("username", "User")

    try:
        if intent == "greeting":
            reply = handle_greeting()

        elif intent == "help":
            reply = handle_help()

        elif intent == "create":
            reply = handle_create(message, db, user_id)

        elif intent == "update":
            reply = handle_update(message, db, user_id)

        elif intent == "delete":
            reply = handle_delete(message, db, user_id)

        elif intent == "list":
            reply = handle_list(message, db, user_id)

        elif intent == "status":
            reply = handle_status(db, user_id)

        else:
            reply = handle_unknown(message)

        return ChatbotResponse(reply=f"{reply}\n\n— {username}")

    except Exception as e:
        return ChatbotResponse(
            reply=f"❌ Something went wrong.\n{str(e)}\n\n— {username}"
        )


def normalize_with_ai(message: str) -> str:
    """
    Uses LLM to rewrite user input into
    a clean, command-like sentence.
    """
    # pseudo-code
    response = llm_call(  # pyright: ignore[reportUndefinedVariable]
        system_prompt="""
        Convert user messages into clear task commands.
        Do NOT invent IDs.
        Do NOT confirm actions.
        Keep it short.
        """,
        user_prompt=message
    )
    return response
