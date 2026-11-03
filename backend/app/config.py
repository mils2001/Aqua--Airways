import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = "sqlite:///aqua_airways.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = 3600

    # Safaricom Daraja configuration
    DARAJA_BASE_URL = os.getenv(
        "DARAJA_BASE_URL",
        "https://sandbox.safaricom.co.ke"
    )
    DARAJA_CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY")
    DARAJA_CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET")
    DARAJA_SHORTCODE = os.getenv("DARAJA_SHORTCODE")
    DARAJA_PASSKEY = os.getenv("DARAJA_PASSKEY")
    DARAJA_CALLBACK_URL = os.getenv("DARAJA_CALLBACK_URL")

    # Flutterwave configuration
    FLUTTERWAVE_BASE_URL = os.getenv(
        "FLUTTERWAVE_BASE_URL",
        "https://api.flutterwave.com/v3"
    )
    FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")
    FLUTTERWAVE_WEBHOOK_HASH = os.getenv("FLUTTERWAVE_WEBHOOK_HASH")
	
