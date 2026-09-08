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


def get_csrf_token(client, path="/login"):
    response = client.get(path)
    page = response.get_data(as_text=True)

    match = re.search(
        r'name="csrf_token"[^>]*value="([^"]+)"',
        page,
    )

    assert match is not None
    return match.group(1)


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


def login_test_user(client, app):
    create_test_user(app)

    response = client.post(
        "/login",
        data={
            "username": "dhairya",
            "password": "securepassword",
            "csrf_token": get_csrf_token(client, "/login"),
        },
    )

    assert response.status_code == 302


def test_home_redirects_anonymous_user_to_login(client):
    response = client.get("/home")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_root_redirects_anonymous_user_to_login(client):
    response = client.get("/")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_authenticated_user_can_access_home(client, app):
    login_test_user(client, app)

    response = client.get("/home")

    assert response.status_code == 200
    assert b"Home" in response.data


def test_authenticated_user_can_access_root(client, app):
    login_test_user(client, app)

    response = client.get("/")

    assert response.status_code == 200
    assert b"Home" in response.data


def test_about_is_public(client):
    response = client.get("/about")

    assert response.status_code == 200


def test_authenticated_user_can_logout(client, app):
    login_test_user(client, app)

    csrf_token = get_csrf_token(client, "/home")

    response = client.post(
        "/logout",
        data={"csrf_token": csrf_token},
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with client.session_transaction() as session:
        assert session.get("_user_id") is None


def test_anonymous_user_cannot_logout(client):
    csrf_token = get_csrf_token(client, "/login")

    response = client.post(
        "/logout",
        data={"csrf_token": csrf_token},
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_without_csrf_token_is_rejected(client, app):
    login_test_user(client, app)

    response = client.post("/logout")

    assert response.status_code == 400


def test_logout_with_invalid_csrf_token_is_rejected(client, app):
    login_test_user(client, app)

    response = client.post(
        "/logout",
        data={"csrf_token": "invalid-token"},
    )

    assert response.status_code == 400