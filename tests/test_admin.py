"""Authorization and API tests."""
from tests.conftest import login


def test_normal_user_cannot_access_admin(client, normal_user):
    login(client, "norm@example.com", "userpass")
    resp = client.get("/admin/")
    assert resp.status_code == 403


def test_admin_can_access_admin(client, admin_user):
    login(client, "admin@example.com", "adminpass")
    resp = client.get("/admin/")
    assert resp.status_code == 200


def test_anonymous_redirected_from_admin(client):
    resp = client.get("/admin/", follow_redirects=False)
    assert resp.status_code == 302  # redirected to login


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "UP"


def test_api_books_empty(client):
    resp = client.get("/api/books")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_api_book_not_found(client):
    resp = client.get("/api/books/999")
    assert resp.status_code == 404
