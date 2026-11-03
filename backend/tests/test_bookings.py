
def create_flight_and_schedule(client):
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
            "available_seats": 10
        }
    )

    assert schedule_response.status_code == 201

    return schedule_response.get_json()["schedule"]["id"]


def booking_payload(schedule_id, seats=2):
    return {
        "schedule_id": schedule_id,
        "seats_booked": seats
    }


def test_create_booking_successfully(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["booking"]["seats_booked"] == 2
    assert data["booking"]["total_amount"] == 17000
    assert data["booking"]["status"] == "PENDING"
    assert data["booking"]["seat_numbers"] == [1, 2]
    assert len(data["booking"]["booking_reference"]) == 20


def test_bookings_receive_distinct_seats_and_references(client, auth_token):
    schedule_id = create_flight_and_schedule(client)
    headers = {"Authorization": "Bearer " + auth_token}

    first_response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id),
        headers=headers
    )
    second_response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id),
        headers=headers
    )

    assert first_response.status_code == 201, first_response.get_json()
    assert second_response.status_code == 201, second_response.get_json()
    first = first_response.get_json()["booking"]
    second = second_response.get_json()["booking"]

    assert first["seat_numbers"] == [1, 2]
    assert second["seat_numbers"] == [3, 4]
    assert first["booking_reference"] != second["booking_reference"]


def test_create_booking_without_token(client):
    response = client.post(
        "/api/bookings",
        json={"schedule_id": 1, "seats_booked": 2}
    )

    assert response.status_code == 401


def test_create_booking_invalid_seat_count(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id, 0),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 400


def test_create_booking_nonexistent_schedule(client, auth_token):
    response = client.post(
        "/api/bookings",
        json=booking_payload(999),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 404


def test_create_booking_insufficient_seats(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id, 11),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 409


def test_get_passenger_bookings(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    client.post(
        "/api/bookings",
        json=booking_payload(schedule_id),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    response = client.get(
        "/api/bookings",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["count"] == 1


def test_get_single_booking(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    create_response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    booking_id = create_response.get_json()["booking"]["id"]

    response = client.get(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    assert response.get_json()["booking"]["id"] == booking_id


def test_get_nonexistent_booking(client, auth_token):
    response = client.get(
        "/api/bookings/999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 404


def test_cancel_booking_and_restore_seats(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    create_response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id, 2),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    booking_id = create_response.get_json()["booking"]["id"]

    response = client.patch(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    assert response.get_json()["booking"]["status"] == "CANCELLED"

    schedule_response = client.get(
        f"/api/flights/1/schedules"
    )

    schedule = schedule_response.get_json()["schedules"][0]

    assert schedule["available_seats"] == 10

    replacement = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id, 2),
        headers={"Authorization": "Bearer " + auth_token}
    )

    assert replacement.status_code == 201
    assert replacement.get_json()["booking"]["seat_numbers"] == [1, 2]


def test_cancel_booking_twice(client, auth_token):
    schedule_id = create_flight_and_schedule(client)

    create_response = client.post(
        "/api/bookings",
        json=booking_payload(schedule_id),
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    booking_id = create_response.get_json()["booking"]["id"]

    first_cancel = client.patch(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    second_cancel = client.patch(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert first_cancel.status_code == 200
    assert second_cancel.status_code == 409
