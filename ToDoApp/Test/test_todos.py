from fastapi import status
from Test.utils import client, test_user, test_todo, TestingSessionLocal
from models import ToDoItem as Todos

def test_read_all_authenticated(test_user, test_todo):
    response = client.get("/todos/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 1
    todo = data[0]
    assert todo["id"] == test_todo.id
    assert todo["title"] == test_todo.title
    assert todo["description"] == test_todo.description
    assert todo["priority"] == test_todo.priority
    assert todo["complete"] == test_todo.complete
    assert todo["owner_id"] == test_user.id

def test_create_todo(test_user):
    payload = {
        "title": "New Todo",
        "description": "Test creation",
        "priority": 3,
        "owner_id": test_user.id
    }
    response = client.post("/todos/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["owner_id"] == test_user.id

def test_update_todo(test_user, test_todo):
    payload = {"title": "Updated Todo"}
    response = client.put(f"/todos/{test_todo.id}", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == payload["title"]

def test_delete_todo(test_user, test_todo):
    response = client.delete(f"/todos/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == test_todo.id).first()
    assert model is None
    db.close()
