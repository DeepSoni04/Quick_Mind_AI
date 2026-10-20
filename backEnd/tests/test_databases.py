import pytest
from app.core.encryption import encrypt_secret, decrypt_secret
from app.services.database_service import DatabaseService


def test_credential_encryption():
    raw_pass = "SuperSecretP@ssw0rd123"
    encrypted = encrypt_secret(raw_pass)

    assert encrypted != raw_pass
    assert len(encrypted) > 20

    decrypted = decrypt_secret(encrypted)
    assert decrypted == raw_pass


def test_mongodb_uri_validation_valid():
    ok, err = DatabaseService._validate_mongodb_uri(
        "mongodb://root:secret@127.0.0.1:27017/college_db"
    )
    assert ok, err


def test_mysql_param_validation_valid():
    ok, err = DatabaseService._validate_mysql_params({
        "host": "127.0.0.1",
        "port": 3306,
        "database_name": "college_db",
    })
    assert ok, err
