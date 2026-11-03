
from unittest.mock import patch


def create_booking(client, auth_token):
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
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert booking_response.status_code == 201
    return booking_response.get_json()["booking"]["id"]


def payment_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


def create_mpesa_payment(client, auth_token):
    booking_id = create_booking(client, auth_token)

    response = client.post(
        "/api/payments",
        json={
            "booking_id": booking_id,
            "payment_method": "MPESA"
        },
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 201
    return response.get_json()["payment"]["id"]


def test_create_payment_successfully(client, auth_token):
    booking_id = create_booking(client, auth_token)

    response = client.post(
        "/api/payments",
        json={
            "booking_id": booking_id,
            "payment_method": "MPESA"
        },
        headers=payment_headers(auth_token)
    )

    data = response.get_json()

    assert response.status_code == 201
    assert data["status"] == "success"
    assert data["payment"]["booking_id"] == booking_id
    assert data["payment"]["amount"] == 17000
    assert data["payment"]["currency"] == "KES"
    assert data["payment"]["payment_method"] == "MPESA"
    assert data["payment"]["status"] == "PENDING"


def test_create_payment_without_token(client):
    response = client.post(
        "/api/payments",
        json={
            "booking_id": 1,
            "payment_method": "MPESA"
        }
    )

    assert response.status_code == 401


def test_create_payment_invalid_method(client, auth_token):
    booking_id = create_booking(client, auth_token)

    response = client.post(
        "/api/payments",
        json={
            "booking_id": booking_id,
            "payment_method": "CRYPTO"
        },
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 400


def test_create_payment_nonexistent_booking(client, auth_token):
    response = client.post(
        "/api/payments",
        json={
            "booking_id": 999,
            "payment_method": "MPESA"
        },
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 404


def test_prevent_duplicate_payment(client, auth_token):
    booking_id = create_booking(client, auth_token)

    payload = {
        "booking_id": booking_id,
        "payment_method": "MPESA"
    }

    first_response = client.post(
        "/api/payments",
        json=payload,
        headers=payment_headers(auth_token)
    )

    second_response = client.post(
        "/api/payments",
        json=payload,
        headers=payment_headers(auth_token)
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_get_passenger_payments(client, auth_token):
    booking_id = create_booking(client, auth_token)

    client.post(
        "/api/payments",
        json={
            "booking_id": booking_id,
            "payment_method": "CARD"
        },
        headers=payment_headers(auth_token)
    )

    response = client.get(
        "/api/payments",
        headers=payment_headers(auth_token)
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["count"] == 1


def test_get_single_payment(client, auth_token):
    booking_id = create_booking(client, auth_token)

    create_response = client.post(
        "/api/payments",
        json={
            "booking_id": booking_id,
            "payment_method": "BANK_TRANSFER"
        },
        headers=payment_headers(auth_token)
    )

    payment_id = create_response.get_json()["payment"]["id"]

    response = client.get(
        f"/api/payments/{payment_id}",
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 200
    assert response.get_json()["payment"]["id"] == payment_id


def test_get_nonexistent_payment(client, auth_token):
    response = client.get(
        "/api/payments/999",
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 404


@patch("app.routes.payments.initiate_stk_push")
def test_initiate_mpesa_payment_successfully(
    mock_stk_push, client, auth_token
):
    payment_id = create_mpesa_payment(client, auth_token)

    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_TEST123",
        "MerchantRequestID": "merchant_TEST123"
    }

    response = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers=payment_headers(auth_token)
    )

    data = response.get_json()

    assert response.status_code == 202
    assert data["status"] == "success"
    assert data["payment_id"] == payment_id
    assert data["attempt_id"] is not None
    assert data["payment_status"] == "PENDING"

    mock_stk_push.assert_called_once()


def test_mpesa_payment_requires_authentication(client):
    response = client.post(
        "/api/payments/1/mpesa",
        json={"phone_number": "254700000000"}
    )

    assert response.status_code == 401


def test_mpesa_payment_rejects_invalid_phone(client, auth_token):
    payment_id = create_mpesa_payment(client, auth_token)

    response = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "0700000000"},
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 400


def test_mpesa_payment_rejects_non_mpesa_payment(
    client, auth_token
):
    booking_id = create_booking(client, auth_token)

    payment_response = client.post(
        "/api/payments",
        json={
            "booking_id": booking_id,
            "payment_method": "CARD"
        },
        headers=payment_headers(auth_token)
    )

    payment_id = payment_response.get_json()["payment"]["id"]

    response = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 400


@patch("app.routes.payments.initiate_stk_push")
def test_prevent_duplicate_active_mpesa_attempt(
    mock_stk_push, client, auth_token
):
    payment_id = create_mpesa_payment(client, auth_token)

    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_TEST456",
        "MerchantRequestID": "merchant_TEST456"
    }

    first_response = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers=payment_headers(auth_token)
    )

    second_response = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers=payment_headers(auth_token)
    )

    assert first_response.status_code == 202
    assert second_response.status_code == 409
    mock_stk_push.assert_called_once()


@patch("app.routes.payments.initiate_stk_push")
def test_mpesa_provider_rejection_does_not_mark_attempt_initiated(
    mock_stk_push, client, auth_token
):
    payment_id = create_mpesa_payment(client, auth_token)

    mock_stk_push.return_value = {
        "ResponseCode": "1",
        "ResponseDescription": "Request rejected"
    }

    response = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers=payment_headers(auth_token)
    )

    assert response.status_code == 502
    assert response.get_json()["status"] == "error"
