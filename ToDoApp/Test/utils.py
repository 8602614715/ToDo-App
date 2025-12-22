import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from routers import auth
from main import app
from models import Base, Users, ToDoItem
from routers.todos import get_db
from passlib.context import CryptContext
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# ----------------------------
# DATABASE SETUP
# ----------------------------
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# ----------------------------
# DEPENDENCY OVERRIDES
# ----------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# ----------------------------
# CLIENT
# ----------------------------
client = TestClient(app)

# ----------------------------
# FIXTURES
# ----------------------------
@pytest.fixture(autouse=True)
def clean_database():
    """Reset DB before each test"""
    db = TestingSessionLocal()
    db.query(ToDoItem).delete()
    db.query(Users).delete()
    db.commit()
    db.close()
    yield

@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    db.query(Users).filter(Users.username=="testuser").delete()
    db.query(Users).filter(Users.email=="user@example.com").delete()
    db.commit()

    user = Users(
        email="user@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        role="user",
        hashed_password=bcrypt_context.hash("not_used"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Override auth
    def override_get_current_user():
        return {"username": user.username, "user_id": user.id, "user_role": user.role}
    app.dependency_overrides[auth.get_current_user] = override_get_current_user

    yield user
    db.close()

@pytest.fixture
def test_admin():
    db = TestingSessionLocal()
    db.query(Users).filter(Users.username=="admin").delete()
    db.query(Users).filter(Users.email=="admin@example.com").delete()
    db.commit()

    admin = Users(
        email="admin@example.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        role="admin",
        hashed_password="not_used",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    # Override auth
    def _override_current_admin():
        return {"username": admin.username, "user_id": admin.id, "user_role": admin.role}
    app.dependency_overrides[auth.get_current_user] = _override_current_admin

    yield admin
    db.close()

@pytest.fixture
def test_todo(request):
    """Create a todo for either test_admin or test_user dynamically"""
    db = TestingSessionLocal()

    # Pick owner dynamically
    owner = request.getfixturevalue("test_admin") if "test_admin" in request.fixturenames else request.getfixturevalue("test_user")

    # Remove existing todos for this owner
    db.query(ToDoItem).filter(ToDoItem.owner_id == owner.id).delete()
    db.commit()

    todo = ToDoItem(
        title="Learn to code!",
        description="Need to learn everyday!",
        priority=5,
        complete=False,
        owner_id=owner.id
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    yield todo
    db.close()
