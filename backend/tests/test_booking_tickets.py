from unittest.mock import patch

from app.extensions import db
from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt


def create_pending_mpesa_payment(client, auth_token):
    headers = {"Authorization": "Bearer " + auth_token}
    flight_response = client.post(
        "/api/flights",
        json={
            "flight_number": "AQ201",
            "origin": "Nairobi",
            "destination": "Kisumu",
            "origin_code": "NBO",
            "destination_code": "KIS",
            "base_price": 8500,
            "total_seats": 30
        }
    )
    flight_id = flight_response.get_json()["flight"]["id"]
    schedule_response = client.post(
        f"/api/flights/{flight_id}/schedules",
        json={
            "departure_at": "2026-12-10T08:00:00Z",
            "arrival_at": "2026-12-10T09:00:00Z",
            "available_seats": 20
        }
    )
    schedule_id = schedule_response.get_json()["schedule"]["id"]
    booking_response = client.post(
        "/api/bookings",
        json={"schedule_id": schedule_id, "seats_booked": 2},
        headers=headers
    )
    booking_id = booking_response.get_json()["booking"]["id"]
    payment_response = client.post(
        "/api/payments",
        json={"booking_id": booking_id, "payment_method": "MPESA"},
        headers=headers
    )

    return payment_response.get_json()["payment"]["id"], booking_id


def callback_payload(
    checkout_id,
    merchant_id,
    result_code=0,
    amount=17000,
    receipt="QWE123"
):
    callback = {
        "MerchantRequestID": merchant_id,
        "CheckoutRequestID": checkout_id,
        "ResultCode": result_code,
        "ResultDesc": "Success" if result_code == 0 else "Cancelled"
    }

    if result_code == 0:
        callback["CallbackMetadata"] = {
            "Item": [
                {"Name": "Amount", "Value": amount},
                {"Name": "MpesaReceiptNumber", "Value": receipt}
            ]
        }

    return {"Body": {"stkCallback": callback}}


@patch("app.routes.payments.initiate_stk_push")
def test_successful_payment_confirms_booking_and_creates_pdf_ticket(
    mock_stk_push, client, auth_token
):
    payment_id, booking_id = create_pending_mpesa_payment(client, auth_token)
    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_TICKET123",
        "MerchantRequestID": "merchant_TICKET123"
    }
    initiation = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers={"Authorization": "Bearer " + auth_token}
    )
    attempt_id = initiation.get_json()["attempt_id"]

    callback = client.post(
        "/api/payments/daraja/callback",
        json=callback_payload(
            "ws_CO_TICKET123",
            "merchant_TICKET123"
        )
    )
    ticket = client.get(
        f"/api/bookings/{booking_id}/ticket",
        headers={"Authorization": "Bearer " + auth_token}
    )

    assert callback.status_code == 200
    assert db.session.get(Payment, payment_id).booking.status == "CONFIRMED"
    assert db.session.get(PaymentAttempt, attempt_id).status == "SUCCEEDED"
    assert ticket.status_code == 200
    assert ticket.mimetype == "application/pdf"
    assert ticket.data.startswith(b"%PDF")


@patch("app.routes.payments.initiate_stk_push")
def test_mismatched_payment_does_not_confirm_booking(
    mock_stk_push, client, auth_token
):
    payment_id, booking_id = create_pending_mpesa_payment(client, auth_token)
    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_AMOUNT",
        "MerchantRequestID": "merchant_AMOUNT"
    }
    client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers={"Authorization": "Bearer " + auth_token}
    )

    callback = client.post(
        "/api/payments/daraja/callback",
        json=callback_payload(
            "ws_CO_AMOUNT",
            "merchant_AMOUNT",
            amount=1
        )
    )
    ticket = client.get(
        f"/api/bookings/{booking_id}/ticket",
        headers={"Authorization": "Bearer " + auth_token}
    )

    assert callback.status_code == 400
    assert db.session.get(Payment, payment_id).booking.status == "PENDING"
    assert ticket.status_code == 409


@patch("app.routes.payments.initiate_stk_push")
def test_failed_payment_can_be_retried(
    mock_stk_push, client, auth_token
):
    payment_id, _ = create_pending_mpesa_payment(client, auth_token)
    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_FAILED",
        "MerchantRequestID": "merchant_FAILED"
    }
    client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers={"Authorization": "Bearer " + auth_token}
    )

    callback = client.post(
        "/api/payments/daraja/callback",
        json=callback_payload(
            "ws_CO_FAILED",
            "merchant_FAILED",
            result_code=1032
        )
    )
    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_RETRY",
        "MerchantRequestID": "merchant_RETRY"
    }
    retry = client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers={"Authorization": "Bearer " + auth_token}
    )

    assert callback.status_code == 200
    assert retry.status_code == 202
    assert mock_stk_push.call_count == 2


@patch("app.routes.payments.initiate_stk_push")
def test_cancelling_confirmed_booking_marks_refund_and_releases_seats(
    mock_stk_push, client, auth_token
):
    payment_id, booking_id = create_pending_mpesa_payment(client, auth_token)
    mock_stk_push.return_value = {
        "ResponseCode": "0",
        "CheckoutRequestID": "ws_CO_CANCEL",
        "MerchantRequestID": "merchant_CANCEL"
    }
    client.post(
        f"/api/payments/{payment_id}/mpesa",
        json={"phone_number": "254700000000"},
        headers={"Authorization": "Bearer " + auth_token}
    )
    client.post(
        "/api/payments/daraja/callback",
        json=callback_payload("ws_CO_CANCEL", "merchant_CANCEL")
    )
    booking = db.session.get(Payment, payment_id).booking
    schedule_id = booking.schedule_id

    cancellation = client.patch(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": "Bearer " + auth_token}
    )
    replacement = client.post(
        "/api/bookings",
        json={"schedule_id": schedule_id, "seats_booked": 2},
        headers={"Authorization": "Bearer " + auth_token}
    )

    assert cancellation.status_code == 200
    assert db.session.get(Payment, payment_id).status == "REFUND_REQUIRED"
    assert replacement.status_code == 201
    assert replacement.get_json()["booking"]["seat_numbers"] == [1, 2]
