from fastapi import status
from Test.utils import client, test_admin, test_todo, TestingSessionLocal
from models import ToDoItem as Todos

def test_admin_read_all_authenticated(test_admin, test_todo):
    response = client.get("/admin/todo")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Look for the fixture todo in the returned list
    todo = next((t for t in data if t["id"] == test_todo.id), None)
    assert todo is not None
    assert todo["title"] == test_todo.title
    assert todo["description"] == test_todo.description
    assert todo["priority"] == test_todo.priority
    assert todo["complete"] == test_todo.complete
    assert todo["owner_id"] == test_admin.id

def test_admin_delete_todo(test_admin, test_todo):
    response = client.delete(f"/admin/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion from DB
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == test_todo.id).all()
    assert model is None
    db.close()

def test_admin_delete_todo_not_found(test_admin):
    response = client.delete("/admin/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Todo not found.'}
