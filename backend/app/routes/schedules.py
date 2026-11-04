
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.flight import Flight
from app.models.flight_schedule import FlightSchedule


schedules_bp = Blueprint("schedules", __name__)
VALID_STATUSES = {
    "SCHEDULED",
    "DELAYED",
    "CANCELLED",
    "COMPLETED"
}


def parse_datetime(value):
    if not isinstance(value, str):
        raise ValueError

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError

    return parsed.astimezone(timezone.utc)


def format_datetime(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.isoformat()


def schedule_data(schedule):
    return {
        "id": schedule.id,
        "flight_id": schedule.flight_id,
        "flight_number": schedule.flight.flight_number,
        "departure_at": format_datetime(schedule.departure_at),
        "arrival_at": format_datetime(schedule.arrival_at),
        "available_seats": schedule.available_seats,
        "status": schedule.status,
        "created_at": format_datetime(schedule.created_at)
    }


@schedules_bp.route(
    "/api/flights/<int:flight_id>/schedules",
    methods=["POST"]
)
def create_schedule(flight_id):
    flight = db.session.get(Flight, flight_id)

    if not flight:
        return jsonify({
            "status": "error",
            "message": "Flight not found."
        }), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON object is required."
        }), 400

    required_fields = [
        "departure_at",
        "arrival_at",
        "available_seats"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"{field} is required."
            }), 400

    try:
        departure_at = parse_datetime(data["departure_at"])
        arrival_at = parse_datetime(data["arrival_at"])

        available_seats = data["available_seats"]

        if isinstance(available_seats, bool):
            raise ValueError

        available_seats = int(available_seats)

        if available_seats < 0:
            raise ValueError

        if available_seats > flight.total_seats:
            return jsonify({
                "status": "error",
                "message": (
                    "Available seats cannot exceed the flight's "
                    "total seat capacity."
                )
            }), 400

        if arrival_at <= departure_at:
            return jsonify({
                "status": "error",
                "message": "Arrival time must be after departure time."
            }), 400

        status = str(data.get("status", "SCHEDULED")).strip().upper()

        if status not in VALID_STATUSES:
            return jsonify({
                "status": "error",
                "message": "Invalid schedule status."
            }), 400

    except (ValueError, TypeError, OverflowError):
        return jsonify({
            "status": "error",
            "message": (
                "Invalid schedule data. Provide valid ISO 8601 "
                "dates with timezone information and a whole number "
                "of available seats."
            )
        }), 400

    schedule = FlightSchedule(
        flight_id=flight.id,
        departure_at=departure_at,
        arrival_at=arrival_at,
        available_seats=available_seats,
        status=status
    )

    try:
        db.session.add(schedule)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Flight schedule created successfully.",
            "schedule": schedule_data(schedule)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to create the flight schedule."
        }), 400

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "An error occurred while creating the schedule."
        }), 500


@schedules_bp.route(
    "/api/flights/<int:flight_id>/schedules",
    methods=["GET"]
)
def get_flight_schedules(flight_id):
    flight = db.session.get(Flight, flight_id)

    if not flight:
        return jsonify({
            "status": "error",
            "message": "Flight not found."
        }), 404

    schedules = (
        FlightSchedule.query
        .filter_by(flight_id=flight_id)
        .order_by(FlightSchedule.departure_at.asc())
        .all()
    )

    return jsonify({
        "status": "success",
        "flight_id": flight.id,
        "flight_number": flight.flight_number,
        "count": len(schedules),
        "schedules": [
            schedule_data(schedule)
            for schedule in schedules
        ]
    }), 200


@schedules_bp.route(
    "/api/schedules/<int:schedule_id>",
    methods=["GET"]
)
def get_schedule(schedule_id):
    schedule = db.session.get(FlightSchedule, schedule_id)

    if not schedule:
        return jsonify({
            "status": "error",
            "message": "Flight schedule not found."
        }), 404

    return jsonify({
        "status": "success",
        "schedule": schedule_data(schedule)
    }), 200

