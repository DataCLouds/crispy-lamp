import pytest

from app import create_app


@pytest.fixture
def client():
    """Create a test client for sending requests to the Flask app."""
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_login_get(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Login GET works YAY :D"


def test_login_post(client):
    response = client.post("/login")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Login POST works Hooray :)"


def test_register_get(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Register GET works YAY :D"


def test_register_post(client):
    response = client.post("/register")

    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Register POST woorks HOORAY :)"


def test_login_rejects_put_request(client):
    response = client.put("/login")

    assert response.status_code == 405