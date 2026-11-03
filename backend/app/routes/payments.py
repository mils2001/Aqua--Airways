import uuid

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment


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

