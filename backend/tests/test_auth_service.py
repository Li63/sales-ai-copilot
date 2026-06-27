from app.services.auth_service import AuthService


def test_auth_service_hashes_and_verifies_password():
    service = AuthService("secret")

    password_hash = service.hash_password("secret123")

    assert service.verify_password("secret123", password_hash)
    assert not service.verify_password("bad", password_hash)


def test_auth_service_creates_parseable_signed_token():
    service = AuthService("secret")

    token = service.create_token(42)
    payload = service.parse_token(token)

    assert payload is not None
    assert payload.user_id == 42


def test_auth_service_rejects_tampered_token():
    service = AuthService("secret")

    token = service.create_token(42) + "x"

    assert service.parse_token(token) is None
