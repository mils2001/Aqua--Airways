
from app.extensions import db
from app.models.booking import Booking


def create_completed_booking(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    flight_response = client.post(
        "/api/flights",
        json={
            "flight_number": "AQ101",
            "origin": "Nairobi",
            "destination": "Mombasa",
            "origin_code": "NBO",
            "destination_code": "MBA",
            "base_price": 8500,
            "total_seats": 30
        }
    )

    assert flight_response.status_code == 201
    flight_id = flight_response.get_json()["flight"]["id"]

    schedule_response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json={
            "departure_at": "2026-12-10T08:00:00Z",
            "arrival_at": "2026-12-10T09:15:00Z",
            "available_seats": 20
        }
    )

    assert schedule_response.status_code == 201
    schedule_id = schedule_response.get_json()["schedule"]["id"]

    booking_response = client.post(
        "/api/bookings",
        json={
            "schedule_id": schedule_id,
            "seats_booked": 2
        },
        headers=headers
    )

    assert booking_response.status_code == 201
    booking_id = booking_response.get_json()["booking"]["id"]

    with client.application.app_context():
        booking = db.session.get(Booking, booking_id)
        booking.status = "COMPLETED"
        db.session.commit()

    return schedule_id


def rating_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def submit_rating(client, auth_token, schedule_id):
    return client.post(
        "/api/ratings",
        json={
            "schedule_id": schedule_id,
            "rating": 5,
            "comment": "Excellent flight experience."
        },
        headers=rating_headers(auth_token)
    )


def test_create_rating_successfully(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)

    response = submit_rating(client, auth_token, schedule_id)
    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["rating"]["rating"] == 5
    assert data["rating"]["comment"] == "Excellent flight experience."


def test_create_rating_without_token(client):
    response = client.post(
        "/api/ratings",
        json={
            "schedule_id": 1,
            "rating": 5,
            "comment": "Great flight."
        }
    )

    assert response.status_code == 401


def test_create_rating_without_completed_booking(client, auth_token):
    flight_response = client.post(
        "/api/flights",
        json={
            "flight_number": "AQ102",
            "origin": "Nairobi",
            "destination": "Kisumu",
            "origin_code": "NBO",
            "destination_code": "KIS",
            "base_price": 6000,
            "total_seats": 20
        }
    )

    flight_id = flight_response.get_json()["flight"]["id"]

    schedule_response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json={
            "departure_at": "2026-12-11T08:00:00Z",
            "arrival_at": "2026-12-11T09:00:00Z",
            "available_seats": 20
        }
    )

    schedule_id = schedule_response.get_json()["schedule"]["id"]

    response = submit_rating(client, auth_token, schedule_id)

    assert response.status_code == 403


def test_create_rating_invalid_value(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)

    response = client.post(
        "/api/ratings",
        json={
            "schedule_id": schedule_id,
            "rating": 6,
            "comment": "Invalid rating."
        },
        headers=rating_headers(auth_token)
    )

    assert response.status_code == 400


def test_create_duplicate_rating(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)

    first_response = submit_rating(client, auth_token, schedule_id)
    second_response = submit_rating(client, auth_token, schedule_id)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_get_all_ratings(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)
    submit_rating(client, auth_token, schedule_id)

    response = client.get("/api/ratings")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["count"] == 1


def test_get_ratings_by_schedule(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)
    submit_rating(client, auth_token, schedule_id)

    response = client.get(
        f"/api/ratings?schedule_id={schedule_id}"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["count"] == 1
    assert data["ratings"][0]["schedule_id"] == schedule_id


def test_get_single_rating(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)
    create_response = submit_rating(client, auth_token, schedule_id)

    rating_id = create_response.get_json()["rating"]["id"]

    response = client.get(f"/api/ratings/{rating_id}")

    assert response.status_code == 200
    assert response.get_json()["rating"]["id"] == rating_id


def test_update_rating(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)
    create_response = submit_rating(client, auth_token, schedule_id)

    rating_id = create_response.get_json()["rating"]["id"]

    response = client.patch(
        f"/api/ratings/{rating_id}",
        json={
            "rating": 4,
            "comment": "Updated flight experience."
        },
        headers=rating_headers(auth_token)
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["rating"]["rating"] == 4
    assert data["rating"]["comment"] == "Updated flight experience."


def test_delete_rating(client, auth_token):
    schedule_id = create_completed_booking(client, auth_token)
    create_response = submit_rating(client, auth_token, schedule_id)

    rating_id = create_response.get_json()["rating"]["id"]

    response = client.delete(
        f"/api/ratings/{rating_id}",
        headers=rating_headers(auth_token)
    )

    assert response.status_code == 200

    check_response = client.get(f"/api/ratings/{rating_id}")

    assert check_response.status_code == 404

