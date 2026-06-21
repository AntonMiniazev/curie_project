from apps.api.core.security import (
    create_access_token,
    create_random_token,
    create_streamlit_embed_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_verifies_correct_password_and_rejects_wrong_password() -> None:
    password_hash = hash_password("CorrectHorse123!")

    assert password_hash != "CorrectHorse123!"
    assert verify_password("CorrectHorse123!", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_access_token_contains_expected_claims() -> None:
    token = create_access_token(
        user_id="11111111-1111-4111-8111-111111111111",
        email="demo@example.com",
        roles=["store_fontaine"],
    )

    claims = decode_access_token(token)

    assert claims["sub"] == "11111111-1111-4111-8111-111111111111"
    assert claims["email"] == "demo@example.com"
    assert claims["roles"] == ["store_fontaine"]
    assert claims["type"] == "access"
    assert "iat" in claims
    assert "exp" in claims


def test_streamlit_embed_token_contains_expected_scope_claims() -> None:
    token = create_streamlit_embed_token(
        user_id="11111111-1111-4111-8111-111111111111",
        email="demo@example.com",
        roles=["store_fontaine"],
    )

    claims = decode_access_token(token)

    assert claims["sub"] == "11111111-1111-4111-8111-111111111111"
    assert claims["email"] == "demo@example.com"
    assert claims["roles"] == ["store_fontaine"]
    assert claims["type"] == "streamlit_embed"
    assert "iat" in claims
    assert "exp" in claims


def test_refresh_token_helpers_create_random_tokens_and_stable_hashes() -> None:
    token = create_random_token()
    other_token = create_random_token()

    assert token != other_token
    assert hash_token(token).startswith("sha256:")
    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token
