
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.flight import Flight

flights_bp = Blueprint("flights", __name__)


@flights_bp.route("/api/flights", methods=["POST"])
def create_flight():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "flight_number",
        "origin",
        "destination",
        "origin_code",
        "destination_code",
        "base_price",
        "total_seats"
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "status": "error",
                "message": f"{field} is required."
            }), 400

    try:
        base_price = float(data["base_price"])
        total_seats = int(data["total_seats"])

        if base_price < 0 or total_seats <= 0:
            raise ValueError

        if total_seats != float(data["total_seats"]):
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid price or seat capacity."
        }), 400

    flight_number = str(data["flight_number"]).strip()

    if Flight.query.filter_by(flight_number=flight_number).first():
        return jsonify({
            "status": "error",
            "message": "Flight number already exists."
        }), 409

    flight = Flight(
        flight_number=flight_number,
        origin=str(data["origin"]).strip(),
        destination=str(data["destination"]).strip(),
        origin_code=str(data["origin_code"]).strip().upper(),
        destination_code=str(data["destination_code"]).strip().upper(),
        base_price=base_price,
        total_seats=total_seats,
        destination_image=data.get("destination_image")
    )

    try:
        db.session.add(flight)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Flight created successfully.",
            "flight": {
                "id": flight.id,
                "flight_number": flight.flight_number,
                "origin": flight.origin,
                "destination": flight.destination,
                "origin_code": flight.origin_code,
                "destination_code": flight.destination_code,
                "base_price": float(flight.base_price),
                "total_seats": flight.total_seats,
                "destination_image": flight.destination_image
            }
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Flight number already exists."
        }), 409

    except Exception:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Unable to create flight."
        }), 500


@flights_bp.route("/api/flights", methods=["GET"])
def get_flights():
    flights = Flight.query.order_by(Flight.id.desc()).all()

    return jsonify({
        "status": "success",
        "count": len(flights),
        "flights": [
            {
                "id": flight.id,
                "flight_number": flight.flight_number,
                "origin": flight.origin,
                "destination": flight.destination,
                "origin_code": flight.origin_code,
                "destination_code": flight.destination_code,
                "base_price": float(flight.base_price),
                "total_seats": flight.total_seats,
                "destination_image": flight.destination_image
            }
            for flight in flights
        ]
    }), 200


@flights_bp.route("/api/flights/<int:flight_id>", methods=["GET"])
def get_flight(flight_id):
    flight = db.session.get(Flight, flight_id)

    if not flight:
        return jsonify({
            "status": "error",
            "message": "Flight not found."
        }), 404

    return jsonify({
        "status": "success",
        "flight": {
            "id": flight.id,
            "flight_number": flight.flight_number,
            "origin": flight.origin,
            "destination": flight.destination,
            "origin_code": flight.origin_code,
            "destination_code": flight.destination_code,
            "base_price": float(flight.base_price),
            "total_seats": flight.total_seats,
            "destination_image": flight.destination_image
        }
    }), 200
