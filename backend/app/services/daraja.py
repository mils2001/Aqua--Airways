import base64
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import requests
from requests.auth import HTTPBasicAuth

from flask import current_app


def get_access_token():
    consumer_key = current_app.config.get("DARAJA_CONSUMER_KEY")
    consumer_secret = current_app.config.get("DARAJA_CONSUMER_SECRET")
    base_url = current_app.config.get("DARAJA_BASE_URL")

    if not consumer_key or not consumer_secret:
        raise ValueError("Daraja credentials are not configured.")

    url = f"{base_url}/oauth/v1/generate"

    response = requests.get(
        url,
        params={"grant_type": "client_credentials"},
        auth=HTTPBasicAuth(consumer_key, consumer_secret),
        timeout=30
    )

    response.raise_for_status()

    result = response.json()
    access_token = result.get("access_token")

    if not access_token:
        raise ValueError("Daraja did not return an access token.")

    return access_token


def generate_password(shortcode, passkey, timestamp):
    raw_password = f"{shortcode}{passkey}{timestamp}"

    return base64.b64encode(
        raw_password.encode("utf-8")
    ).decode("utf-8")


def initiate_stk_push(phone_number, amount, account_reference, description):
    shortcode = current_app.config.get("DARAJA_SHORTCODE")
    passkey = current_app.config.get("DARAJA_PASSKEY")
    callback_url = current_app.config.get("DARAJA_CALLBACK_URL")
    base_url = current_app.config.get("DARAJA_BASE_URL")

    if not all([shortcode, passkey, callback_url]):
        raise ValueError("Daraja STK Push configuration is incomplete.")

    amount = Decimal(str(amount))

    if amount <= 0 or amount != amount.to_integral_value():
        raise ValueError("Payment amount must be a positive whole KES amount.")

    amount = int(amount)

    timestamp = datetime.now(
        ZoneInfo("Africa/Nairobi")
    ).strftime("%Y%m%d%H%M%S")

    password = generate_password(
        shortcode,
        passkey,
        timestamp
    )

    access_token = get_access_token()

    url = f"{base_url}/mpesa/stkpush/v1/processrequest"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference,
        "TransactionDesc": description
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()
