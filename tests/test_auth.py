"""Authentication tests."""
from app.models import User
from tests.conftest import login


def test_register_success(client, db):
    resp = client.post(
        "/register",
        data={
            "name": "New User",
            "email": "new@example.com",
            "password": "secret1",
            "confirm": "secret1",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert db.session.query(User).filter_by(email="new@example.com").first() is not None


def test_register_duplicate_email(client, normal_user):
    resp = client.post(
        "/register",
        data={
            "name": "Dup",
            "email": "norm@example.com",
            "password": "secret1",
            "confirm": "secret1",
        },
        follow_redirects=True,
    )
    assert b"already exists" in resp.data


def test_login_success(client, normal_user):
    resp = login(client, "norm@example.com", "userpass")
    assert resp.status_code == 200
    assert b"Logout" in resp.data


def test_login_failure(client, normal_user):
    resp = login(client, "norm@example.com", "wrongpass")
    assert b"Invalid email or password" in resp.data


def test_logout(client, normal_user):
    login(client, "norm@example.com", "userpass")
    resp = client.get("/logout", follow_redirects=True)
    assert b"logged out" in resp.data


def test_password_is_hashed(normal_user):
    assert normal_user.password_hash != "userpass"
    assert normal_user.check_password("userpass")
