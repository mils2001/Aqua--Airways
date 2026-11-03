from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import update

from app.extensions import db
from app.models.booking import Booking
from app.models.flight_schedule import FlightSchedule


bookings_bp = Blueprint("bookings", __name__)


def get_current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def booking_data(booking):
    schedule = booking.schedule
    flight = schedule.flight

    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "seats_booked": booking.seats_booked,
        "total_amount": float(booking.total_amount),
        "status": booking.status,
        "created_at": booking.created_at.isoformat(),
        "schedule": {
            "id": schedule.id,
            "departure_at": schedule.departure_at.isoformat(),
            "arrival_at": schedule.arrival_at.isoformat(),
            "status": schedule.status
        },
        "flight": {
            "id": flight.id,
            "flight_number": flight.flight_number,
            "origin": flight.origin,
            "destination": flight.destination,
            "origin_code": flight.origin_code,
            "destination_code": flight.destination_code
        }
    }


@bookings_bp.route("/api/bookings", methods=["POST"])
@jwt_required()
def create_booking():
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

    schedule_id = data.get("schedule_id")
    seats_booked = data.get("seats_booked")

    if isinstance(schedule_id, bool) or isinstance(seats_booked, bool):
        return jsonify({
            "status": "error",
            "message": "Schedule ID and seats must be valid integers."
        }), 400

    try:
        schedule_id = int(schedule_id)
        seats_booked = int(seats_booked)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Schedule ID and seats must be valid integers."
        }), 400

    if schedule_id <= 0 or seats_booked <= 0:
        return jsonify({
            "status": "error",
            "message": "Schedule ID and seats must be greater than zero."
        }), 400

    schedule = db.session.get(FlightSchedule, schedule_id)

    if not schedule:
        return jsonify({
            "status": "error",
            "message": "Flight schedule not found."
        }), 404

    if schedule.status != "SCHEDULED":
        return jsonify({
            "status": "error",
            "message": "This flight is not available for booking."
        }), 400

    price = Decimal(str(schedule.flight.base_price)) * Decimal(seats_booked)

    try:
        result = db.session.execute(
            update(FlightSchedule)
            .where(
                FlightSchedule.id == schedule_id,
                FlightSchedule.status == "SCHEDULED",
                FlightSchedule.available_seats >= seats_booked
            )
            .values(
                available_seats=FlightSchedule.available_seats - seats_booked
            )
        )

        if result.rowcount != 1:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Not enough seats are available."
            }), 409

        booking = Booking(
            user_id=user_id,
            schedule_id=schedule_id,
            seats_booked=seats_booked,
            total_amount=price,
            status="PENDING"
        )

        db.session.add(booking)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Booking created successfully.",
            "booking": booking_data(booking)
        }), 201

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to create booking."
        }), 500


@bookings_bp.route("/api/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    bookings = (
        Booking.query
        .filter_by(user_id=user_id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    return jsonify({
        "status": "success",
        "count": len(bookings),
        "bookings": [booking_data(booking) for booking in bookings]
    }), 200


@bookings_bp.route("/api/bookings/<int:booking_id>", methods=["GET"])
@jwt_required()
def get_booking(booking_id):
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user_id
    ).first()

    if not booking:
        return jsonify({
            "status": "error",
            "message": "Booking not found."
        }), 404

    return jsonify({
        "status": "success",
        "booking": booking_data(booking)
    }), 200


@bookings_bp.route("/api/bookings/<int:booking_id>/cancel", methods=["PATCH"])
@jwt_required()
def cancel_booking(booking_id):
    user_id = get_current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token."
        }), 401

    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user_id
    ).first()

    if not booking:
        return jsonify({
            "status": "error",
            "message": "Booking not found."
        }), 404

    if booking.status == "CANCELLED":
        return jsonify({
            "status": "error",
            "message": "This booking has already been cancelled."
        }), 409

    if booking.status not in ("PENDING", "CONFIRMED"):
        return jsonify({
            "status": "error",
            "message": "This booking cannot be cancelled."
        }), 400

    try:
        booking.status = "CANCELLED"
        booking.schedule.available_seats += booking.seats_booked

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Booking cancelled successfully.",
            "booking": booking_data(booking)
        }), 200

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to cancel booking."
        }), 500
