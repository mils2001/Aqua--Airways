
def create_flight(client):
    response = client.post(
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

    assert response.status_code == 201
    return response.get_json()["flight"]["id"]


def create_schedule_payload():
    return {
        "departure_at": "2026-12-10T08:00:00Z",
        "arrival_at": "2026-12-10T09:15:00Z",
        "available_seats": 25
    }


def test_create_schedule_successfully(client):
    flight_id = create_flight(client)

    response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json=create_schedule_payload()
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["schedule"]["flight_number"] == "AQ101"
    assert data["schedule"]["available_seats"] == 25
    assert data["schedule"]["status"] == "SCHEDULED"


def test_create_schedule_for_nonexistent_flight(client):
    response = client.post(
        "/api/flights/999/schedules",
        json=create_schedule_payload()
    )

    assert response.status_code == 404


def test_create_schedule_missing_field(client):
    flight_id = create_flight(client)
    payload = create_schedule_payload()
    del payload["arrival_at"]

    response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json=payload
    )

    assert response.status_code == 400


def test_create_schedule_invalid_datetime(client):
    flight_id = create_flight(client)
    payload = create_schedule_payload()
    payload["departure_at"] = "invalid-date"

    response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json=payload
    )

    assert response.status_code == 400


def test_create_schedule_arrival_before_departure(client):
    flight_id = create_flight(client)
    payload = create_schedule_payload()
    payload["arrival_at"] = "2026-12-10T07:00:00Z"

    response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json=payload
    )

    assert response.status_code == 400


def test_create_schedule_exceeding_seat_capacity(client):
    flight_id = create_flight(client)
    payload = create_schedule_payload()
    payload["available_seats"] = 31

    response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json=payload
    )

    assert response.status_code == 400


def test_create_schedule_invalid_status(client):
    flight_id = create_flight(client)
    payload = create_schedule_payload()
    payload["status"] = "UNKNOWN"

    response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json=payload
    )

    assert response.status_code == 400


def test_get_flight_schedules(client):
    flight_id = create_flight(client)

    client.post(
        f"/api/flights/{flight_id}/schedules",
        json=create_schedule_payload()
    )

    response = client.get(
        f"/api/flights/{flight_id}/schedules"
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["count"] == 1
    assert data["flight_number"] == "AQ101"


def test_get_nonexistent_schedule(client):
    response = client.get("/api/schedules/999")

    assert response.status_code == 404
