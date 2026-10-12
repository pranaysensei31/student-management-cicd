import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app import app, init_db
@pytest.fixture
def client():

    db_fd, db_path = tempfile.mkstemp()

    app.config["TESTING"] = True

    import app as application
    application.DATABASE = db_path

    init_db()

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


def test_login_page(client):
    response = client.get("/login")

    assert response.status_code == 200


def test_invalid_login(client):
    response = client.post(
        "/login",
        data={
            "username": "wrong",
            "password": "wrong"
        }
    )

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data


def test_valid_login(client):
    response = client.post(
        "/login",
        data={
            "username": "admin",
            "password": "admin123"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_dashboard_requires_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_students_requires_login(client):
    response = client.get("/students")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]