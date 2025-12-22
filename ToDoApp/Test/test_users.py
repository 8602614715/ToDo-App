# Test/test_users.py

from fastapi import status
from routers.users import get_db
from routers import auth
from Test.utils import client, override_get_db, test_user
from main import app
# Override DB dependency (test_user fixture will auto-override auth)
app.dependency_overrides[get_db] = override_get_db

def test_return_user(test_user):
    response = client.get("/user")
    assert response.status_code == status.HTTP_200_OK
    # Use the values from test_user fixture
    assert response.json()['username'] == test_user.username
    assert response.json()['email'] == test_user.email
    assert response.json()['first_name'] == test_user.first_name
    assert response.json()['last_name'] == test_user.last_name
    assert response.json()['role'] == test_user.role

def test_change_password_success(test_user):
    response = client.put("/user/password", json={
        "password": "not_used", 
        "new_password": "newpassword"
    })
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_change_password_invalid_current_password(test_user):
    response = client.put("/user/password", json={
        "password": "wrong_password",
        "new_password": "newpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail': 'Error on password change'}

def test_change_phone_number_success(test_user):
    response = client.put("/user/phonenumber/2222222222")
    assert response.status_code == status.HTTP_204_NO_CONTENT
