import re

import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture
def app():
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=True,
    )

    with app.app_context():
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def get_csrf_token(client, path="/register"):
    response = client.get(path)
    page = response.get_data(as_text=True)

    match = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"',
        page,
    )

    assert match is not None
    return match.group(1)


def registration_data(client, **overrides):
    data = {
        "username": "dhairya",
        "email": "dhairya@example.com",
        "password": "securepassword",
        "confirm_password": "securepassword",
        "first_name": "Dhairya",
        "csrf_token": get_csrf_token(client),
    }

    data.update(overrides)
    return data

def login_data(client, **overrides):
    data = {
        "username": "dhairya",
        "password": "securepassword",
        "csrf_token": get_csrf_token(client, "/login"),
    }

    data.update(overrides)
    return data


def create_test_user(app):
    with app.app_context():
        user = User(
            username="dhairya",
            email="dhairya@example.com",
            first_name="Dhairya",
        )
        user.set_password("securepassword")

        db.session.add(user)
        db.session.commit()


def test_register_get_displays_form(client):
    response = client.get("/register")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Create an Account" in page
    assert 'name="username"' in page
    assert 'name="email"' in page
    assert 'name="password"' in page
    assert 'name="confirm_password"' in page
    assert 'name="first_name"' in page
    assert 'name="csrf_token"' in page


def test_valid_registration_creates_user(client, app):
    response = client.post(
        "/register",
        data=registration_data(client),
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    with app.app_context():
        user = User.query.filter_by(username="dhairya").first()

        assert user is not None
        assert user.email == "dhairya@example.com"
        assert user.first_name == "Dhairya"
        assert user.password_hash != "securepassword"
        assert user.check_password("securepassword") is True


def test_duplicate_username_is_rejected(client):
    first_response = client.post(
        "/register",
        data=registration_data(client),
    )

    assert first_response.status_code == 302

    response = client.post(
        "/register",
        data=registration_data(
            client,
            email="different@example.com",
        ),
    )

    assert response.status_code == 200
    assert b"Username already exists." in response.data


def test_duplicate_email_is_rejected(client):
    first_response = client.post(
        "/register",
        data=registration_data(client),
    )

    assert first_response.status_code == 302

    response = client.post(
        "/register",
        data=registration_data(
            client,
            username="different-user",
        ),
    )

    assert response.status_code == 200
    assert b"Email already exists." in response.data


def test_invalid_email_is_rejected(client):
    response = client.post(
        "/register",
        data=registration_data(
            client,
            email="not-an-email",
        ),
    )

    assert response.status_code == 200
    assert b"Invalid email address." in response.data


def test_short_password_is_rejected(client):
    response = client.post(
        "/register",
        data=registration_data(
            client,
            password="short",
            confirm_password="short",
        ),
    )

    assert response.status_code == 200
    assert (
        b"Field must be between 8 and 64 characters long."
        in response.data
    )


def test_mismatched_passwords_are_rejected(client):
    response = client.post(
        "/register",
        data=registration_data(
            client,
            confirm_password="differentpassword",
        ),
    )

    assert response.status_code == 200
    assert b"Passwords must match" in response.data


def test_missing_csrf_token_is_rejected(client):
    data = {
        "username": "dhairya",
        "email": "dhairya@example.com",
        "password": "securepassword",
        "confirm_password": "securepassword",
        "first_name": "Dhairya",
    }

    response = client.post("/register", data=data)

    assert response.status_code == 400


def test_invalid_csrf_token_is_rejected(client):
    data = registration_data(
        client,
        csrf_token="invalid-token",
    )

    response = client.post("/register", data=data)

    assert response.status_code == 400


def test_register_rejects_put_request(client):
    response = client.put("/register")

    assert response.status_code == 405

def test_login_get_displays_form(client):
    response = client.get("/login")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Login" in page
    assert 'name="username"' in page
    assert 'name="password"' in page
    assert 'name="csrf_token"' in page

def test_valid_login_logs_user_in(client, app):
    create_test_user(app)

    response = client.post(
        "/login",
        data=login_data(client),
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session.get("_user_id") is not None

def test_login_rejects_wrong_password(client, app):
    create_test_user(app)

    response = client.post(
        "/login",
        data=login_data(
            client,
            password="wrongpassword",
        ),
    )

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data

def test_login_rejects_unknown_username(client):
    response = client.post(
        "/login",
        data=login_data(
            client,
            username="unknown-user",
        ),
    )

    assert response.status_code == 200
    assert b"Invalid username or password." in response.data

def test_login_rejects_invalid_form(client):
    response = client.post(
        "/login",
        data=login_data(
            client,
            username="",
        ),
    )

    assert response.status_code == 200
    assert b"This field is required." in response.data


def test_login_without_csrf_token_is_rejected(client):
    response = client.post(
        "/login",
        data={
            "username": "dhairya",
            "password": "securepassword",
        },
    )

    assert response.status_code == 400


def test_login_with_invalid_csrf_token_is_rejected(client):
    response = client.post(
        "/login",
        data=login_data(
            client,
            csrf_token="invalid-token",
        ),
    )

    assert response.status_code == 400


def test_login_rejects_put_request(client):
    response = client.put("/login")

    assert response.status_code == 405

