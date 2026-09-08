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
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Login" in page
    assert 'name="username"' in page
    assert 'name="password"' in page
    assert 'name="csrf_token"' in page


def test_login_post_without_csrf_token_is_rejected(client):
    response = client.post("/login")

    assert response.status_code == 400

def test_login_post_with_invalid_csrf_token_is_rejected(client):
    response = client.post(
        "/login",
        data={"csrf_token": "invalid-token"},
    )

    assert response.status_code == 400

def test_register_get(client):
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

def test_register_post_without_csrf_token_is_rejected(client):
    response = client.post("/register")

    assert response.status_code == 400

def test_register_post_with_invalid_csrf_token_is_rejected(client):
    response = client.post(
        "/register",
        data={"csrf_token": "invalid-token"},
    )

    assert response.status_code == 400

def test_login_rejects_put_request(client):
    response = client.put("/login")

    assert response.status_code == 405

def test_register_rejects_put_request(client):
    response = client.put("/register")

    assert response.status_code == 405