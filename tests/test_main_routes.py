import pytest

from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app = create_app()
    app.config["TESTING"] = True

    return app.test_client()


def test_home_root_route(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Welcome to AI Personal Journal" in response.data


def test_home_route(client):
    response = client.get("/home")

    assert response.status_code == 200
    assert b"Welcome to AI Personal Journal" in response.data


def test_root_and_home_render_same_page(client):
    root_response = client.get("/")
    home_response = client.get("/home")

    assert root_response.status_code == 200
    assert home_response.status_code == 200
    assert root_response.data == home_response.data


def test_about_route(client):
    response = client.get("/about")

    assert response.status_code == 200
    assert b"About AI Personal Journal" in response.data