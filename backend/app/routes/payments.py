
import uuid
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.payment_attempt import PaymentAttempt
from app.services.daraja import initiate_stk_push

payments_bp = Blueprint("payments", __name__)


def get_current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def payment_data(payment):
    return {
        "id": payment.id,
        "booking_id": payment.booking_id,
        "booking_reference": payment.booking.booking_reference,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "payment_method": payment.payment_method,
        "transaction_reference": payment.transaction_reference,
        "status": payment.status,
        "created_at": payment.created_at.isoformat()
    }


@payments_bp.route("/api/payments", methods=["POST"])
@jwt_required()
def create_payment():
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON object is required."
        }), 400

    booking_id = data.get("booking_id")
    payment_method = data.get("payment_method")

    if isinstance(booking_id, bool):
        return jsonify({
            "status": "error",
            "message": "Booking ID must be a valid integer."
        }), 400

    try:
        booking_id = int(booking_id)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Booking ID must be a valid integer."
        }), 400

    if booking_id <= 0:
        return jsonify({
            "status": "error",
            "message": "Booking ID must be greater than zero."
        }), 400

    if not isinstance(payment_method, str):
        return jsonify({
            "status": "error",
            "message": "A valid payment method is required."
        }), 400

    payment_method = payment_method.strip().upper()

    allowed_methods = {"MPESA", "CARD", "BANK_TRANSFER"}

    if payment_method not in allowed_methods:
        return jsonify({
            "status": "error",
            "message": "Choose MPESA, CARD, or BANK_TRANSFER."
        }), 400

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user_id
    ).first()

    if not booking:
        return jsonify({
            "status": "error",
            "message": "Booking not found."
        }), 404

    if booking.status != "PENDING":
        return jsonify({
            "status": "error",
            "message": "Only pending bookings can be paid."
        }), 409

    existing_payment = Payment.query.filter_by(
        booking_id=booking.id
    ).first()

    if existing_payment:
        return jsonify({
            "status": "error",
            "message": "A payment record already exists for this booking."
        }), 409

    payment = Payment(
        booking_id=booking.id,
        amount=booking.total_amount,
        currency="KES",
        payment_method=payment_method,
        transaction_reference=f"AQP-{uuid.uuid4().hex[:16].upper()}",
        status="PENDING"
    )

    try:
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Payment record created. Payment confirmation is pending.",
            "payment": payment_data(payment)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "A payment record already exists for this booking."
        }), 409

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to create payment record."
        }), 500


@payments_bp.route("/api/payments", methods=["GET"])
@jwt_required()
def get_payments():
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    payments = (
        Payment.query
        .join(Booking)
        .filter(Booking.user_id == user_id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return jsonify({
        "status": "success",
        "count": len(payments),
        "payments": [payment_data(payment) for payment in payments]
    }), 200


@payments_bp.route("/api/payments/<int:payment_id>", methods=["GET"])
@jwt_required()
def get_payment(payment_id):
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    payment = (
        Payment.query
        .join(Booking)
        .filter(
            Payment.id == payment_id,
            Booking.user_id == user_id
        )
        .first()
    )

    if not payment:
        return jsonify({
            "status": "error",
            "message": "Payment not found."
        }), 404

    return jsonify({
        "status": "success",
        "payment": payment_data(payment)
    }), 200


@payments_bp.route(
    "/api/payments/<int:payment_id>/mpesa",
    methods=["POST"]
)
@jwt_required()
def initiate_mpesa_payment(payment_id):
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON object is required."
        }), 400

    phone_number = data.get("phone_number")

    if not isinstance(phone_number, str):
        return jsonify({
            "status": "error",
            "message": "A valid phone number is required."
        }), 400

    phone_number = phone_number.strip().replace("+", "")

    if (
        len(phone_number) != 12
        or not phone_number.startswith("254")
        or not phone_number.isdigit()
    ):
        return jsonify({
            "status": "error",
            "message": "Use a Kenyan phone number in 254XXXXXXXXX format."
        }), 400

    payment = (
        Payment.query
        .join(Booking)
        .filter(
            Payment.id == payment_id,
            Booking.user_id == user_id
        )
        .first()
    )

    if not payment:
        return jsonify({
            "status": "error",
            "message": "Payment not found."
        }), 404

    if payment.payment_method != "MPESA":
        return jsonify({
            "status": "error",
            "message": "This payment was not created for M-Pesa."
        }), 400

    if payment.booking.status != "PENDING":
        return jsonify({
            "status": "error",
            "message": "Only pending bookings can be paid."
        }), 409

    if payment.status not in {"PENDING", "FAILED"}:
        return jsonify({
            "status": "error",
            "message": "This payment cannot be initiated in its current state."
        }), 409

    if payment.currency != "KES":
        return jsonify({
            "status": "error",
            "message": "M-Pesa payments must use KES."
        }), 400

    active_attempt = PaymentAttempt.query.filter(
        PaymentAttempt.payment_id == payment.id,
        PaymentAttempt.provider == "DARAJA",
        PaymentAttempt.status.in_(["PENDING", "INITIATED"])
    ).first()

    if active_attempt:
        return jsonify({
            "status": "error",
            "message": "An M-Pesa payment attempt is already active."
        }), 409

    attempt = PaymentAttempt(
        payment_id=payment.id,
        provider="DARAJA",
        status="PENDING"
    )
    payment.status = "PENDING"

    try:
        db.session.add(attempt)
        db.session.commit()

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to create payment attempt."
        }), 500

    try:
        result = initiate_stk_push(
            phone_number=phone_number,
            amount=payment.amount,
            account_reference=payment.transaction_reference,
            description="Aqua Airways booking payment"
        )

        if (
            not isinstance(result, dict)
            or result.get("ResponseCode") != "0"
            or not result.get("CheckoutRequestID")
            or not result.get("MerchantRequestID")
        ):
            attempt.status = "INITIATION_FAILED"
            db.session.commit()

            return jsonify({
                "status": "error",
                "message": "The payment provider did not accept the request."
            }), 502

        attempt.provider_reference = result["CheckoutRequestID"]
        attempt.transaction_reference = result["MerchantRequestID"]
        attempt.status = "INITIATED"

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "STK Push request submitted. Awaiting payment confirmation.",
            "payment_id": payment.id,
            "attempt_id": attempt.id,
            "payment_status": payment.status
        }), 202

    except Exception:
        db.session.rollback()

        attempt = db.session.get(PaymentAttempt, attempt.id)

        if attempt:
            attempt.status = "INITIATION_UNKNOWN"
            db.session.commit()

        return jsonify({
            "status": "error",
            "message": "The provider response could not be confirmed. Check the attempt before retrying.",
            "attempt_id": attempt.id if attempt else None
        }), 502


@payments_bp.route(
    "/api/payments/daraja/callback",
    methods=["POST"]
)
def daraja_payment_callback():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON callback is required."
        }), 400

    body = data.get("Body")
    callback = body.get("stkCallback") if isinstance(body, dict) else None
    if not isinstance(callback, dict):
        return jsonify({
            "status": "error",
            "message": "The M-Pesa callback payload is invalid."
        }), 400

    checkout_id = callback.get("CheckoutRequestID")
    merchant_id = callback.get("MerchantRequestID")
    result_code = callback.get("ResultCode")
    if (
        not isinstance(checkout_id, str)
        or not checkout_id
        or isinstance(result_code, bool)
        or (
            isinstance(result_code, float)
            and not result_code.is_integer()
        )
    ):
        return jsonify({
            "status": "error",
            "message": "The M-Pesa callback is missing required identifiers."
        }), 400

    try:
        result_code = int(result_code)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "The M-Pesa result code is invalid."
        }), 400

    attempt = PaymentAttempt.query.filter_by(
        provider="DARAJA",
        provider_reference=checkout_id
    ).first()
    if not attempt:
        return jsonify({
            "status": "error",
            "message": "No matching M-Pesa payment attempt was found."
        }), 404

    if attempt.status == "SUCCEEDED":
        return jsonify({
            "status": "success",
            "message": "Payment callback was already processed."
        }), 200

    if attempt.status not in {"PENDING", "INITIATED"}:
        return jsonify({
            "status": "error",
            "message": "This M-Pesa payment attempt is no longer active."
        }), 409

    if (
        not isinstance(merchant_id, str)
        or not merchant_id
        or merchant_id != attempt.transaction_reference
    ):
        return jsonify({
            "status": "error",
            "message": "The M-Pesa callback identifiers do not match."
        }), 400

    payment = attempt.payment
    booking = payment.booking

    if result_code != 0:
        attempt.status = "FAILED"
        payment.status = "FAILED"
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Unable to record the failed payment result."
            }), 500

        return jsonify({
            "status": "success",
            "message": "Payment failure recorded."
        }), 200

    callback_metadata = callback.get("CallbackMetadata")
    items = callback_metadata.get("Item") if isinstance(
        callback_metadata,
        dict
    ) else None
    if not isinstance(items, list):
        items = []

    metadata = {
        item.get("Name"): item.get("Value")
        for item in items
        if isinstance(item, dict) and isinstance(item.get("Name"), str)
    }

    try:
        callback_amount = Decimal(str(metadata["Amount"]))
        receipt_number = metadata["MpesaReceiptNumber"]
    except (KeyError, InvalidOperation, TypeError, ValueError):
        attempt.status = "FAILED"
        payment.status = "FAILED"
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Unable to record the invalid payment callback."
            }), 500
        return jsonify({
            "status": "error",
            "message": "The successful M-Pesa callback lacks payment details."
        }), 400

    if (
        callback_amount != Decimal(str(payment.amount))
        or not isinstance(receipt_number, str)
        or not receipt_number.strip()
    ):
        attempt.status = "FAILED"
        payment.status = "FAILED"
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Unable to record the mismatched payment callback."
            }), 500
        return jsonify({
            "status": "error",
            "message": "The M-Pesa callback payment details do not match."
        }), 400

    attempt.status = "SUCCEEDED"
    attempt.transaction_reference = receipt_number.strip()
    payment.status = "SUCCEEDED"

    if booking.status != "PENDING":
        payment.status = "REFUND_REQUIRED"
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Unable to record the late payment result."
            }), 500

        return jsonify({
            "status": "error",
            "message": (
                "Payment was received after the booking changed status; "
                "a refund is required."
            )
        }), 409

    confirmation = db.session.execute(
        update(Booking)
        .where(
            Booking.id == booking.id,
            Booking.status == "PENDING"
        )
        .values(status="CONFIRMED")
    )

    if confirmation.rowcount != 1:
        payment.status = "REFUND_REQUIRED"
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Unable to record the late payment result."
            }), 500

        return jsonify({
            "status": "error",
            "message": (
                "Payment was received after the booking changed status; "
                "a refund is required."
            )
        }), 409

    booking.status = "CONFIRMED"
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "The M-Pesa receipt was already used."
        }), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to confirm the booking payment."
        }), 500

    return jsonify({
        "status": "success",
        "message": "Payment confirmed and booking confirmed."
    }), 200
