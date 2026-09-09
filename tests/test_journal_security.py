import re
import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import JournalEntry, User


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = True

    with app.app_context():
        db.create_all()
        u1 = User(username="alice", email="alice@example.com")
        u1.set_password("password_alice")
        u2 = User(username="bob", email="bob@example.com")
        u2.set_password("password_bob")
        db.session.add_all([u1, u2])
        db.session.commit()
        app.user_a_id = u1.id
        app.user_b_id = u2.id
        yield app
        db.drop_all()


@pytest.fixture
def auth_client_a(app):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(app.user_a_id)
        sess["_fresh"] = True
    return client


@pytest.fixture
def auth_client_b(app):
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(app.user_b_id)
        sess["_fresh"] = True
    return client


@pytest.fixture
def anon_client(app):
    return app.test_client()


def _extract_csrf_token(html: str) -> str:
    match = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html)
    if not match:
        match = re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']csrf_token["\']', html)
    assert match is not None, f"CSRF token not found in HTML: {html}"
    return match.group(1)


# ---------------------------------------------------------------------------
# Access Control (Authentication) Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,path,data", [
    ("GET", "/journal/", None),
    ("GET", "/journal/new", None),
    ("POST", "/journal/new", {"content": "Hello", "user_emotion": "Happy"}),
    ("GET", "/journal/1", None),
    ("GET", "/journal/1/edit", None),
    ("POST", "/journal/1/edit", {"content": "Updated", "user_emotion": "Neutral"}),
    ("POST", "/journal/1/delete", {}),
])
def test_unauthenticated_requests_redirect_to_login(anon_client, method, path, data):
    if method == "GET":
        response = anon_client.get(path)
    else:
        response = anon_client.post(path, data=data)

    assert response.status_code in (301, 302)
    assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Ownership Authorization Edge Cases
# ---------------------------------------------------------------------------

def test_cross_user_cannot_view_entry_detail(auth_client_a, app):
    with app.app_context():
        bob_entry = JournalEntry(
            user_id=app.user_b_id,
            content="Bob's private note",
            user_emotion="Sad",
        )
        db.session.add(bob_entry)
        db.session.commit()
        entry_id = bob_entry.id

    response = auth_client_a.get(f"/journal/{entry_id}")
    assert response.status_code == 404


def test_cross_user_cannot_view_edit_form(auth_client_a, app):
    with app.app_context():
        bob_entry = JournalEntry(
            user_id=app.user_b_id,
            content="Bob's private draft",
            user_emotion="Neutral",
        )
        db.session.add(bob_entry)
        db.session.commit()
        entry_id = bob_entry.id

    response = auth_client_a.get(f"/journal/{entry_id}/edit")
    assert response.status_code == 404


def test_cross_user_cannot_edit_entry_and_leaves_db_intact(auth_client_a, app):
    with app.app_context():
        bob_entry = JournalEntry(
            user_id=app.user_b_id,
            content="Original Bob content",
            user_emotion="Sad",
        )
        db.session.add(bob_entry)
        db.session.commit()
        entry_id = bob_entry.id

    # Alice gets a valid CSRF token from new entry page
    get_res = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_res.get_data(as_text=True))

    post_res = auth_client_a.post(
        f"/journal/{entry_id}/edit",
        data={
            "csrf_token": token,
            "content": "Maliciously modified by Alice",
            "user_emotion": "Angry",
        },
    )
    assert post_res.status_code == 404

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
        persisted = db.session.scalars(stmt).one()
        assert persisted.content == "Original Bob content"
        assert persisted.user_emotion == "Sad"
        assert persisted.user_id == app.user_b_id


def test_cross_user_cannot_delete_entry_and_leaves_db_intact(auth_client_a, app):
    with app.app_context():
        bob_entry = JournalEntry(
            user_id=app.user_b_id,
            content="Bob entry to protect",
            user_emotion="Neutral",
        )
        db.session.add(bob_entry)
        db.session.commit()
        entry_id = bob_entry.id

    # Alice gets valid CSRF token from new entry page
    get_res = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_res.get_data(as_text=True))

    post_res = auth_client_a.post(
        f"/journal/{entry_id}/delete",
        data={"csrf_token": token},
    )
    assert post_res.status_code == 404

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
        persisted = db.session.scalars(stmt).one_or_none()
        assert persisted is not None
        assert persisted.content == "Bob entry to protect"


# ---------------------------------------------------------------------------
# CSRF Protection Tests
# ---------------------------------------------------------------------------

def test_post_create_entry_without_csrf_is_rejected(auth_client_a, app):
    response = auth_client_a.post(
        "/journal/new",
        data={
            "content": "Unauthorized post without CSRF",
            "user_emotion": "Happy",
        },
    )
    assert response.status_code == 200  # Form validation failure, re-renders form
    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.user_id == app.user_a_id)
        entries = db.session.scalars(stmt).all()
        assert len(entries) == 0


def test_post_create_entry_with_valid_csrf_succeeds(auth_client_a, app):
    get_response = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_response.get_data(as_text=True))

    post_response = auth_client_a.post(
        "/journal/new",
        data={
            "csrf_token": token,
            "content": "Valid CSRF post",
            "user_emotion": "Happy",
        },
        follow_redirects=True,
    )
    assert post_response.status_code == 200
    assert "Journal entry created." in post_response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.user_id == app.user_a_id)
        entries = db.session.scalars(stmt).all()
        assert len(entries) == 1
        assert entries[0].content == "Valid CSRF post"


def test_post_edit_entry_without_csrf_is_rejected(auth_client_a, app):
    with app.app_context():
        entry = JournalEntry(
            user_id=app.user_a_id,
            content="Initial content",
            user_emotion="Neutral",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    response = auth_client_a.post(
        f"/journal/{entry_id}/edit",
        data={
            "content": "Modified without CSRF",
            "user_emotion": "Sad",
        },
    )
    assert response.status_code == 200

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
        persisted = db.session.scalars(stmt).one()
        assert persisted.content == "Initial content"


def test_post_delete_entry_without_csrf_is_rejected(auth_client_a, app):
    with app.app_context():
        entry = JournalEntry(
            user_id=app.user_a_id,
            content="Entry not to be deleted without CSRF",
            user_emotion="Angry",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    response = auth_client_a.post(f"/journal/{entry_id}/delete", data={})
    assert response.status_code == 400

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
        persisted = db.session.scalars(stmt).one_or_none()
        assert persisted is not None


# ---------------------------------------------------------------------------
# Validation Edge Cases
# ---------------------------------------------------------------------------

def test_create_entry_rejects_empty_and_whitespace_content(auth_client_a, app):
    get_res = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_res.get_data(as_text=True))

    for invalid_content in ["", "   ", "\n\t  \n"]:
        response = auth_client_a.post(
            "/journal/new",
            data={
                "csrf_token": token,
                "content": invalid_content,
                "user_emotion": "Happy",
            },
        )
        assert response.status_code == 200
        assert "Content is required" in response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.user_id == app.user_a_id)
        entries = db.session.scalars(stmt).all()
        assert len(entries) == 0


def test_create_entry_rejects_overlimit_content(auth_client_a, app):
    get_res = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_res.get_data(as_text=True))

    overlimit_content = "A" * 5001
    response = auth_client_a.post(
        "/journal/new",
        data={
            "csrf_token": token,
            "content": overlimit_content,
            "user_emotion": "Happy",
        },
    )
    assert response.status_code == 200
    assert "Content must be between 1 and 5000 characters" in response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.user_id == app.user_a_id)
        entries = db.session.scalars(stmt).all()
        assert len(entries) == 0


def test_create_entry_rejects_invalid_emotion(auth_client_a, app):
    get_res = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_res.get_data(as_text=True))

    response = auth_client_a.post(
        "/journal/new",
        data={
            "csrf_token": token,
            "content": "Valid content with invalid emotion",
            "user_emotion": "SuperExcitedInvalidEmotion",
        },
    )
    assert response.status_code == 200
    assert "Not a valid choice" in response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.user_id == app.user_a_id)
        entries = db.session.scalars(stmt).all()
        assert len(entries) == 0


def test_nonexistent_entry_id_returns_404(auth_client_a):
    non_existent_id = 999999
    assert auth_client_a.get(f"/journal/{non_existent_id}").status_code == 404
    assert auth_client_a.get(f"/journal/{non_existent_id}/edit").status_code == 404

    # With CSRF token
    get_res = auth_client_a.get("/journal/new")
    token = _extract_csrf_token(get_res.get_data(as_text=True))

    assert (
        auth_client_a.post(
            f"/journal/{non_existent_id}/edit",
            data={"csrf_token": token, "content": "Sample", "user_emotion": "Happy"},
        ).status_code
        == 404
    )
    assert (
        auth_client_a.post(
            f"/journal/{non_existent_id}/delete",
            data={"csrf_token": token},
        ).status_code
        == 404
    )
