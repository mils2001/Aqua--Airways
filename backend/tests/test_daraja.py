import base64

import pytest

from app.services.daraja import (
    generate_password,
    get_access_token,
    initiate_stk_push,
)


def test_generate_password():
    result = generate_password(
        "123456",
        "test-passkey",
        "20261104120000"
    )

    expected = base64.b64encode(
        b"123456test-passkey20261104120000"
    ).decode("utf-8")

    assert result == expected


def test_get_access_token_success(app, monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"access_token": "test-access-token"}

    def mock_get(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(
        "app.services.daraja.requests.get",
        mock_get
    )

    with app.app_context():
        app.config["DARAJA_CONSUMER_KEY"] = "test-key"
        app.config["DARAJA_CONSUMER_SECRET"] = "test-secret"

        token = get_access_token()

    assert token == "test-access-token"


def test_get_access_token_missing_credentials(app):
    with app.app_context():
        app.config["DARAJA_CONSUMER_KEY"] = None
        app.config["DARAJA_CONSUMER_SECRET"] = None

        with pytest.raises(ValueError):
            get_access_token()


def test_stk_push_success(app, monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "ResponseCode": "0",
                "ResponseDescription": "Success"
            }

    def mock_get(*args, **kwargs):
        class TokenResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"access_token": "test-access-token"}

        return TokenResponse()

    def mock_post(*args, **kwargs):
        assert kwargs["json"]["Amount"] == 8500
        assert kwargs["json"]["PhoneNumber"] == "254700000000"
        assert kwargs["headers"]["Authorization"] == (
            "Bearer test-access-token"
        )

        return MockResponse()

    monkeypatch.setattr(
        "app.services.daraja.requests.get",
        mock_get
    )

    monkeypatch.setattr(
        "app.services.daraja.requests.post",
        mock_post
    )

    with app.app_context():
        app.config.update({
            "DARAJA_CONSUMER_KEY": "test-key",
            "DARAJA_CONSUMER_SECRET": "test-secret",
            "DARAJA_SHORTCODE": "123456",
            "DARAJA_PASSKEY": "test-passkey",
            "DARAJA_CALLBACK_URL": "https://example.com/callback",
            "DARAJA_BASE_URL": "https://sandbox.safaricom.co.ke"
        })

        result = initiate_stk_push(
            phone_number="254700000000",
            amount=8500,
            account_reference="AQ-TEST-001",
            description="Aqua Airways test"
        )

    assert result["ResponseCode"] == "0"


def test_stk_push_rejects_decimal_amount(app):
    with app.app_context():
        app.config.update({
            "DARAJA_SHORTCODE": "123456",
            "DARAJA_PASSKEY": "test-passkey",
            "DARAJA_CALLBACK_URL": "https://example.com/callback"
        })

        with pytest.raises(ValueError):
            initiate_stk_push(
                phone_number="254700000000",
                amount=8500.50,
                account_reference="AQ-TEST-002",
                description="Test payment"
            )
