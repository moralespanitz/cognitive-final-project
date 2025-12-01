"""
Tests for security utilities.
"""
import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing():
    """Test password hashing and verification."""
    password = "TestPassword123!"
    hashed = get_password_hash(password)

    # Hash should be different from password
    assert hashed != password

    # Verify correct password
    assert verify_password(password, hashed) is True

    # Verify wrong password
    assert verify_password("WrongPassword", hashed) is False


def test_password_hash_consistency():
    """Test that same password creates different hashes (salt)."""
    password = "SamePassword123!"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Hashes should be different due to salt
    assert hash1 != hash2

    # But both should verify correctly
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_create_access_token():
    """Test creating access token."""
    data = {"sub": "123"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    decoded = decode_token(token)
    assert decoded["sub"] == "123"
    assert decoded["type"] == "access"
    assert "exp" in decoded


def test_create_refresh_token():
    """Test creating refresh token."""
    data = {"sub": "456"}
    token = create_refresh_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    decoded = decode_token(token)
    assert decoded["sub"] == "456"
    assert decoded["type"] == "refresh"
    assert "exp" in decoded


def test_decode_token_invalid():
    """Test decoding invalid token raises error."""
    with pytest.raises(Exception):
        decode_token("invalid-token-string")


def test_token_contains_expiration():
    """Test that tokens have expiration."""
    data = {"sub": "789"}
    token = create_access_token(data)

    decoded = decode_token(token)

    assert "exp" in decoded
    assert isinstance(decoded["exp"], int)
    assert decoded["exp"] > 0
