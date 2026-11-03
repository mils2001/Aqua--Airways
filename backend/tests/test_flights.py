
def create_flight_payload():
    return {
        "flight_number": "AQ101",
        "origin": "Nairobi",
        "destination": "Mombasa",
        "origin_code": "nbo",
        "destination_code": "mba",
        "base_price": 8500,
        "total_seats": 30,
        "destination_image": "https://example.com/mombasa.jpg"
    }


def test_create_flight_successfully(client):
    response = client.post(
        "/api/flights",
        json=create_flight_payload()
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["flight"]["flight_number"] == "AQ101"
    assert data["flight"]["origin_code"] == "NBO"
    assert data["flight"]["destination_code"] == "MBA"


def test_create_flight_missing_field(client):
    payload = create_flight_payload()
    del payload["flight_number"]

    response = client.post("/api/flights", json=payload)

    assert response.status_code == 400


def test_create_flight_invalid_price(client):
    payload = create_flight_payload()
    payload["base_price"] = -100

    response = client.post("/api/flights", json=payload)

    assert response.status_code == 400


def test_create_flight_invalid_seat_capacity(client):
    payload = create_flight_payload()
    payload["total_seats"] = 0

    response = client.post("/api/flights", json=payload)

    assert response.status_code == 400


def test_create_duplicate_flight_number(client):
    payload = create_flight_payload()

    first_response = client.post("/api/flights", json=payload)
    second_response = client.post("/api/flights", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_get_all_flights(client):
    client.post("/api/flights", json=create_flight_payload())

    response = client.get("/api/flights")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["count"] == 1
    assert len(data["flights"]) == 1


def test_get_single_flight(client):
    create_response = client.post(
        "/api/flights",
        json=create_flight_payload()
    )

    flight_id = create_response.get_json()["flight"]["id"]

    response = client.get(f"/api/flights/{flight_id}")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["flight"]["flight_number"] == "AQ101"


def test_get_nonexistent_flight(client):
    response = client.get("/api/flights/999")

    assert response.status_code == 404
    assert response.get_json()["status"] == "error"

