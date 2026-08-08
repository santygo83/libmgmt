"""Shared pytest fixtures."""
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import Role, User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(db):
    user = User(name="Admin", email="admin@example.com", role=Role.ADMIN)
    user.set_password("adminpass")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def normal_user(db):
    user = User(name="Norm", email="norm@example.com", role=Role.USER)
    user.set_password("userpass")
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
