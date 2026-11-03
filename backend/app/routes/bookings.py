from io import BytesIO
from decimal import Decimal

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models.booking import Booking, BookingSeat
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
        "seat_numbers": [
            seat.seat_number for seat in booking.seat_allocations
        ],
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


def create_ticket_pdf(booking):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _, page_height = letter

    pdf.setTitle(f"Aqua Airways ticket {booking.booking_reference}")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, page_height - 54, "Aqua Airways")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(48, page_height - 88, "Passenger ticket")

    pdf.setFont("Helvetica", 11)
    details = [
        ("Booking reference", booking.booking_reference),
        ("Passenger", booking.user.full_name),
        ("Flight", booking.schedule.flight.flight_number),
        (
            "Route",
            (
                f"{booking.schedule.flight.origin} "
                f"({booking.schedule.flight.origin_code}) to "
                f"{booking.schedule.flight.destination} "
                f"({booking.schedule.flight.destination_code})"
            )
        ),
        ("Departure", booking.schedule.departure_at.isoformat()),
        ("Arrival", booking.schedule.arrival_at.isoformat()),
        (
            "Seat numbers",
            ", ".join(
                str(seat.seat_number)
                for seat in booking.seat_allocations
            )
        ),
        ("Booking status", booking.status),
    ]

    y = page_height - 126
    for label, value in details:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(48, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(154, y, str(value).encode("ascii", "replace").decode())
        y -= 24

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(
        48,
        48,
        "Present this ticket and valid identification when boarding."
    )
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


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
        if isinstance(data.get("schedule_id"), float):
            if not data["schedule_id"].is_integer():
                raise ValueError
        seats_booked = int(seats_booked)
        if isinstance(data.get("seats_booked"), float):
            if not data["seats_booked"].is_integer():
                raise ValueError
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

        occupied_seats = {
            seat_number
            for (seat_number,) in db.session.query(
                BookingSeat.seat_number
            ).filter_by(schedule_id=schedule_id).all()
        }
        seat_numbers = [
            seat_number
            for seat_number in range(1, schedule.flight.total_seats + 1)
            if seat_number not in occupied_seats
        ][:seats_booked]

        if len(seat_numbers) != seats_booked:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Unable to allocate the requested seats."
            }), 409

        booking = Booking(
            user_id=user_id,
            schedule_id=schedule_id,
            seats_booked=seats_booked,
            total_amount=price,
            status="PENDING"
        )

        db.session.add(booking)
        db.session.flush()
        booking.seat_allocations.extend(
            BookingSeat(
                schedule_id=schedule_id,
                seat_number=seat_number
            )
            for seat_number in seat_numbers
        )
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Booking created successfully.",
            "booking": booking_data(booking)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "A booking conflict occurred. Please try again."
        }), 409

    except SQLAlchemyError:
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


@bookings_bp.route(
    "/api/bookings/<int:booking_id>/ticket",
    methods=["GET"]
)
@jwt_required()
def get_booking_ticket(booking_id):
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

    if booking.status != "CONFIRMED":
        return jsonify({
            "status": "error",
            "message": "A ticket is available only for confirmed bookings."
        }), 409

    return send_file(
        create_ticket_pdf(booking),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"ticket-{booking.booking_reference}.pdf"
    )


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

    was_confirmed = booking.status == "CONFIRMED"

    try:
        result = db.session.execute(
            update(Booking)
            .where(
                Booking.id == booking.id,
                Booking.user_id == user_id,
                Booking.status.in_(("PENDING", "CONFIRMED"))
            )
            .values(status="CANCELLED")
        )

        if result.rowcount != 1:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "This booking has already changed status."
            }), 409

        db.session.execute(
            update(FlightSchedule)
            .where(FlightSchedule.id == booking.schedule_id)
            .values(
                available_seats=(
                    FlightSchedule.available_seats + booking.seats_booked
                )
            )
        )
        booking.status = "CANCELLED"
        if was_confirmed and booking.payment:
            db.session.refresh(booking.payment)
            if booking.payment.status == "SUCCEEDED":
                booking.payment.status = "REFUND_REQUIRED"
        booking.seat_allocations.clear()

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Booking cancelled successfully.",
            "booking": booking_data(booking)
        }), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to cancel booking."
        }), 500
