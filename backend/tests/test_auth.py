
def test_register_user_successfully(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "John Passenger",
            "email": "john@example.com",
            "password": "Password123"
        }
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["user"]["full_name"] == "John Passenger"
    assert data["user"]["email"] == "john@example.com"


def test_register_duplicate_email(client, registered_user):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Another Passenger",
            "email": "passenger@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 409


def test_register_missing_fields(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "John Passenger"}
    )

    assert response.status_code == 400


def test_register_invalid_email(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "John Passenger",
            "email": "invalid-email",
            "password": "Password123"
        }
    )

    assert response.status_code == 400


def test_register_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "John Passenger",
            "email": "john@example.com",
            "password": "123"
        }
    )

    assert response.status_code == 400


def test_login_successfully(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "passenger@example.com",
            "password": "TestPassword123"
        }
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert "access_token" in data


def test_login_invalid_password(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "passenger@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401


def test_login_unknown_email(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "Password123"
        }
    )

    assert response.status_code == 401


def test_profile_without_token(client):
    response = client.get("/api/auth/profile")

    assert response.status_code == 401


def test_profile_with_valid_token(client, auth_token):
    response = client.get(
        "/api/auth/profile",
        headers={
            "Authorization": f"Bearer {auth_token}"
        }
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["user"]["email"] == "passenger@example.com"

