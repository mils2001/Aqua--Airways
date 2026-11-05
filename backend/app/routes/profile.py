
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User
from app.models.aqua_reward_claim import AquaRewardClaim


profile_bp = Blueprint("profile", __name__)

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
DAILY_REWARD_POINTS = 10


def current_user():
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return None

    return user


def user_data(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "profile_image": user.profile_image,
        "created_at": user.created_at.isoformat()
    }


def reward_summary(user_id):
    claims = AquaRewardClaim.query.filter_by(
        user_id=user_id
    ).order_by(
        AquaRewardClaim.claim_date.desc()
    ).limit(30).all()

    total_points = db.session.query(
        db.func.coalesce(db.func.sum(AquaRewardClaim.points), 0)
    ).filter_by(user_id=user_id).scalar()

    today = datetime.now(timezone.utc).date()

    claimed_today = AquaRewardClaim.query.filter_by(
        user_id=user_id,
        claim_date=today
    ).first() is not None

    return {
        "total_points": int(total_points),
        "daily_reward": DAILY_REWARD_POINTS,
        "claimed_today": claimed_today,
        "next_claim_date": None if not claimed_today else "Tomorrow",
        "claims": [
            {
                "id": claim.id,
                "points": claim.points,
                "claim_date": claim.claim_date.isoformat(),
                "created_at": claim.created_at.isoformat()
            }
            for claim in claims
        ]
    }


@profile_bp.route("/api/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user = current_user()

    if not user:
        return jsonify({
            "status": "error",
            "message": "User account not found or inactive."
        }), 401

    return jsonify({
        "status": "success",
        "user": user_data(user)
    }), 200


@profile_bp.route("/api/profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    user = current_user()

    if not user:
        return jsonify({
            "status": "error",
            "message": "User account not found or inactive."
        }), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON object is required."
        }), 400

    if "full_name" not in data:
        return jsonify({
            "status": "error",
            "message": "Provide full_name to update."
        }), 400

    full_name = data["full_name"]

    if not isinstance(full_name, str):
        return jsonify({
            "status": "error",
            "message": "Full name must be text."
        }), 400

    full_name = full_name.strip()

    if not full_name or len(full_name) > 120:
        return jsonify({
            "status": "error",
            "message": "Full name must contain between 1 and 120 characters."
        }), 400

    user.full_name = full_name

    try:
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Profile updated successfully.",
            "user": user_data(user)
        }), 200

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "Could not update profile."
        }), 500


@profile_bp.route("/api/profile/photo", methods=["POST"])
@jwt_required()
def upload_profile_photo():
    user = current_user()

    if not user:
        return jsonify({
            "status": "error",
            "message": "User account not found or inactive."
        }), 401

    uploaded_file = request.files.get("photo")

    if not uploaded_file:
        return jsonify({
            "status": "error",
            "message": "Select an image using the photo field."
        }), 400

    image_bytes = uploaded_file.read(MAX_IMAGE_SIZE + 1)

    if not image_bytes:
        return jsonify({
            "status": "error",
            "message": "The uploaded file is empty."
        }), 400

    if len(image_bytes) > MAX_IMAGE_SIZE:
        return jsonify({
            "status": "error",
            "message": "Image size cannot exceed 5 MB."
        }), 413

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            if image.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError("Unsupported image format.")

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large.")

            image.verify()

        with Image.open(BytesIO(image_bytes)) as image:
            image = ImageOps.exif_transpose(image)

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large.")

            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")

            upload_directory = (
                Path(current_app.static_folder)
                / "uploads"
                / "profiles"
            )
            upload_directory.mkdir(parents=True, exist_ok=True)

            filename = f"{uuid4().hex}.jpg"
            file_path = upload_directory / filename

            image.save(file_path, format="JPEG", quality=85, optimize=True)

    except (UnidentifiedImageError, OSError, ValueError):
        return jsonify({
            "status": "error",
            "message": "Upload a valid JPEG, PNG or WEBP image."
        }), 400

    old_image = user.profile_image
    user.profile_image = f"/static/uploads/profiles/{filename}"

    try:
        db.session.commit()

        if old_image and old_image.startswith("/static/uploads/profiles/"):
            old_path = Path(current_app.static_folder) / old_image.removeprefix("/static/")
            if old_path.is_file():
                old_path.unlink(missing_ok=True)

        return jsonify({
            "status": "success",
            "message": "Profile photo uploaded successfully.",
            "profile_image": user.profile_image
        }), 200

    except Exception:
        db.session.rollback()
        file_path.unlink(missing_ok=True)

        return jsonify({
            "status": "error",
            "message": "Could not save profile photo."
        }), 500


@profile_bp.route("/api/rewards", methods=["GET"])
@jwt_required()
def get_rewards():
    user = current_user()

    if not user:
        return jsonify({
            "status": "error",
            "message": "User account not found or inactive."
        }), 401

    return jsonify({
        "status": "success",
        "rewards": reward_summary(user.id)
    }), 200


@profile_bp.route("/api/rewards/claim", methods=["POST"])
@jwt_required()
def claim_daily_reward():
    user = current_user()

    if not user:
        return jsonify({
            "status": "error",
            "message": "User account not found or inactive."
        }), 401

    today = datetime.now(timezone.utc).date()

    existing_claim = AquaRewardClaim.query.filter_by(
        user_id=user.id,
        claim_date=today
    ).first()

    if existing_claim:
        return jsonify({
            "status": "error",
            "message": "You have already claimed today's AQUA Points.",
            "rewards": reward_summary(user.id)
        }), 409

    claim = AquaRewardClaim(
        user_id=user.id,
        points=DAILY_REWARD_POINTS,
        claim_date=today
    )

    try:
        db.session.add(claim)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "You claimed 10 AQUA Points successfully.",
            "rewards": reward_summary(user.id)
        }), 201

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "You have already claimed today's AQUA Points.",
            "rewards": reward_summary(user.id)
        }), 409

    except Exception:
        db.session.rollback()

        return jsonify({
            "status": "error",
            "message": "Could not claim AQUA Points."
        }), 500
