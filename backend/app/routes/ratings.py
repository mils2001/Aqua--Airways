
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.booking import Booking
from app.models.passenger_rating import PassengerRating
from app.models.flight_schedule import FlightSchedule


ratings_bp = Blueprint("ratings", __name__)


def current_user_id():
    try:
        return int(get_jwt_identity())
    except (TypeError, ValueError):
        return None


def rating_data(rating):
    return {
        "id": rating.id,
        "user_id": rating.user_id,
        "schedule_id": rating.schedule_id,
        "flight_number": rating.schedule.flight.flight_number,
        "rating": rating.rating,
        "comment": rating.comment,
        "created_at": rating.created_at.isoformat()
    }


@ratings_bp.route("/api/ratings", methods=["POST"])
@jwt_required()
def create_rating():
    user_id = current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid user identity."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON body is required."
        }), 400

    schedule_id = data.get("schedule_id")
    rating_value = data.get("rating")
    comment = data.get("comment", "")

    if isinstance(schedule_id, bool):
        return jsonify({
            "status": "error",
            "message": "A valid schedule_id is required."
        }), 400

    try:
        schedule_id = int(schedule_id)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "A valid schedule_id is required."
        }), 400

    if schedule_id <= 0:
        return jsonify({
            "status": "error",
            "message": "schedule_id must be positive."
        }), 400

    if isinstance(rating_value, bool):
        return jsonify({
            "status": "error",
            "message": "Rating must be a number between 1 and 5."
        }), 400

    try:
        rating_value = float(rating_value)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Rating must be a number between 1 and 5."
        }), 400

    if not 1 <= rating_value <= 5:
        return jsonify({
            "status": "error",
            "message": "Rating must be between 1 and 5."
        }), 400

    if not isinstance(comment, str):
        return jsonify({
            "status": "error",
            "message": "Comment must be text."
        }), 400

    comment = comment.strip()

    if len(comment) > 2000:
        return jsonify({
            "status": "error",
            "message": "Comment cannot exceed 2000 characters."
        }), 400

    schedule = db.session.get(FlightSchedule, schedule_id)

    if not schedule:
        return jsonify({
            "status": "error",
            "message": "Flight schedule not found."
        }), 404

    completed_booking = Booking.query.filter_by(
        user_id=user_id,
        schedule_id=schedule_id,
        status="COMPLETED"
    ).first()

    if not completed_booking:
        return jsonify({
            "status": "error",
            "message": "You can only rate a flight after completing its booking."
        }), 403

    existing_rating = PassengerRating.query.filter_by(
        user_id=user_id,
        schedule_id=schedule_id
    ).first()

    if existing_rating:
        return jsonify({
            "status": "error",
            "message": "You have already rated this flight."
        }), 409

    new_rating = PassengerRating(
        user_id=user_id,
        schedule_id=schedule_id,
        rating=rating_value,
        comment=comment or None
    )

    try:
        db.session.add(new_rating)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Flight rating submitted successfully.",
            "rating": rating_data(new_rating)
        }), 201

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "You have already rated this flight."
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "Could not submit rating."
        }), 500


@ratings_bp.route("/api/ratings", methods=["GET"])
def get_ratings():
    schedule_id = request.args.get("schedule_id")

    query = PassengerRating.query

    if schedule_id is not None:
        try:
            schedule_id = int(schedule_id)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "Invalid schedule_id."
            }), 400

        if schedule_id <= 0:
            return jsonify({
                "status": "error",
                "message": "schedule_id must be positive."
            }), 400

        if not db.session.get(FlightSchedule, schedule_id):
            return jsonify({
                "status": "error",
                "message": "Flight schedule not found."
            }), 404

        query = query.filter_by(schedule_id=schedule_id)

    ratings = query.order_by(
        PassengerRating.created_at.desc()
    ).all()

    return jsonify({
        "status": "success",
        "count": len(ratings),
        "ratings": [rating_data(item) for item in ratings]
    }), 200


@ratings_bp.route("/api/ratings/<int:rating_id>", methods=["GET"])
def get_rating(rating_id):
    rating = db.session.get(PassengerRating, rating_id)

    if not rating:
        return jsonify({
            "status": "error",
            "message": "Rating not found."
        }), 404

    return jsonify({
        "status": "success",
        "rating": rating_data(rating)
    }), 200


@ratings_bp.route("/api/ratings/<int:rating_id>", methods=["PATCH"])
@jwt_required()
def update_rating(rating_id):
    user_id = current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid user identity."
        }), 401

    rating = PassengerRating.query.filter_by(
        id=rating_id,
        user_id=user_id
    ).first()

    if not rating:
        return jsonify({
            "status": "error",
            "message": "Rating not found."
        }), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON body is required."
        }), 400

    if "rating" in data:
        if isinstance(data["rating"], bool):
            return jsonify({
                "status": "error",
                "message": "Rating must be between 1 and 5."
            }), 400

        try:
            value = float(data["rating"])
        except (TypeError, ValueError):
            return jsonify({
                "status": "error",
                "message": "Rating must be between 1 and 5."
            }), 400

        if not 1 <= value <= 5:
            return jsonify({
                "status": "error",
                "message": "Rating must be between 1 and 5."
            }), 400

        rating.rating = value

    if "comment" in data:
        if not isinstance(data["comment"], str):
            return jsonify({
                "status": "error",
                "message": "Comment must be text."
            }), 400

        comment = data["comment"].strip()

        if len(comment) > 2000:
            return jsonify({
                "status": "error",
                "message": "Comment cannot exceed 2000 characters."
            }), 400

        rating.comment = comment or None

    try:
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Rating updated successfully.",
            "rating": rating_data(rating)
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "Could not update rating."
        }), 500


@ratings_bp.route("/api/ratings/<int:rating_id>", methods=["DELETE"])
@jwt_required()
def delete_rating(rating_id):
    user_id = current_user_id()

    if user_id is None:
        return jsonify({
            "status": "error",
            "message": "Invalid user identity."
        }), 401

    rating = PassengerRating.query.filter_by(
        id=rating_id,
        user_id=user_id
    ).first()

    if not rating:
        return jsonify({
            "status": "error",
            "message": "Rating not found."
        }), 404

    try:
        db.session.delete(rating)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Rating deleted successfully."
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "Could not delete rating."
        }), 500
