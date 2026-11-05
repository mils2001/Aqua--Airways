
from app.models import User
 
 
def test_login_success_returns_token(client, make_user, password):
    make_user(email="a@example.com")
    response = client.post("/login", json={"email": "a@example.com",
        "password": password})
    assert response.status_code == 200
    assert "access_token" in response.get_json()
 
 
def test_login_wrong_password_is_401(client, make_user):
    make_user(email="a@example.com")
    response = client.post("/login", json={"email": "a@example.com",
        "password": "nope"})
    assert response.status_code == 401
 
 
def test_login_unknown_email_is_401(client):
    response = client.post("/login", json={"email": "ghost@example.com",
        "password": "whatever"})
    assert response.status_code == 401
 
 
def test_wrong_email_and_wrong_password_give_same_message(client, make_user):
    """So attackers can't tell which emails are registered."""
    make_user(email="a@example.com")
    wrong_password = client.post("/login", json={"email": "a@example.com",
        "password": "nope"})
    wrong_email = client.post("/login", json={"email": "ghost@example.com",
        "password": "nope"})
    assert wrong_password.get_json() == wrong_email.get_json()
 
 
def test_login_with_empty_body_is_rejected(client):
    response = client.post("/login", json={})
    assert response.status_code in (400, 401)
 
 
def test_inactive_user_cannot_login(client, make_user, password):
    make_user(email="off@example.com", is_active=False)
    response = client.post("/login", json={"email": "off@example.com",
        "password": password})
    assert response.status_code == 401
 
 
def test_login_response_never_contains_password_hash(client, make_user, password):
    make_user(email="a@example.com")
    response = client.post("/login", json={"email": "a@example.com",
         "password": password})
    assert "password" not in response.get_data(as_text=True).lower()
 
 
def test_register_cannot_create_admin(client):
    """A client must never be able to choose their own role."""
    response = client.post("/register", json={
        "full_name": "Sneaky User",
        "email": "sneaky@example.com",
        "password": "TestPass123!",
        "role": "admin",        
    })
    assert response.status_code in (200, 201)
 
    user = User.query.filter_by(email="sneaky@example.com").first()
    assert user is not None
    assert user.role == "passenger"
 