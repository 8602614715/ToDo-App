# FastAPI ToDo Application

A simple **ToDo backend application** built using **FastAPI**, with user authentication, CRUD operations, and database integration.  
This project follows a clean backend structure suitable for learning and real-world use.

---

## 📌 Features
- User Registration & Login
- JWT-based Authentication
- Create, Read, Update, Delete (CRUD) ToDo items
- Admin routes
- Alembic database migrations
- HTML templates with static files (CSS & JS)
- Unit tests included

---

## 🗂 Project Structure
fastapi-backend/
│
├── ToDoApp/
│ ├── main.py
│ ├── database.py
│ ├── models.py
│ ├── schemas.py
│ ├── routers/
│ ├── alembic/
│ ├── static/
│ ├── template/
│ └── Test/
│
├── .gitignore
└── README.md

---

## ⚙️ Requirements
- Python 3.9+
- pip
- Virtual environment (recommended)

---

## 🚀 Setup & Run Locally

### 1️⃣ Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate   # Windows

### 2️⃣ install dependencies
```bash
pip install -r requirements.txt  # Windows

### 3️⃣ Run databse migrations
alembic upgrade head

### 4️⃣ Start Server
uvicorn ToDoApp.main:app --reload


