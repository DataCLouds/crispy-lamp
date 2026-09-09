import pytest

from app import create_app
from app.extensions import db
from app.models import User, JournalEntry


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    # Use in-memory SQLite for tests to keep them isolated and fast
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    # Disable CSRF for test posts to simplify form posts
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        # create a test user
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        app.test_user_id = user.id
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    # set session to logged-in user
    with client.session_transaction() as sess:
        sess["_user_id"] = str(app.test_user_id)
        sess["_fresh"] = True
    return client


def test_create_entry_success(client, app):
    resp = client.post("/journal/new", data={
        "content": "Today I wrote tests.",
        "user_emotion": "Happy",
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        entries = JournalEntry.query.filter_by(user_id=app.test_user_id).all()
        assert len(entries) == 1
        assert entries[0].content == "Today I wrote tests."
        assert entries[0].user_emotion == "Happy"


def test_list_visibility_for_owner(client, app):
    with app.app_context():
        # create an entry for another user
        other = User(username="other", email="other@example.com")
        other.set_password("pw")
        db.session.add(other)
        db.session.commit()
        other_entry = JournalEntry(user_id=other.id, content="Other's entry", user_emotion="Sad")
        my_entry = JournalEntry(user_id=app.test_user_id, content="My secret", user_emotion="Neutral")
        db.session.add_all([other_entry, my_entry])
        db.session.commit()

    resp = client.get("/journal/")
    text = resp.get_data(as_text=True)
    assert "My secret" in text
    assert "Other's entry" not in text


def test_detail_success(client, app):
    with app.app_context():
        entry = JournalEntry(user_id=app.test_user_id, content="Detail me", user_emotion="Happy")
        db.session.add(entry)
        db.session.commit()
        eid = entry.id

    resp = client.get(f"/journal/{eid}")
    assert resp.status_code == 200
    assert "Detail me" in resp.get_data(as_text=True)


def test_edit_success(client, app):
    with app.app_context():
        entry = JournalEntry(user_id=app.test_user_id, content="Old content", user_emotion="Neutral")
        db.session.add(entry)
        db.session.commit()
        eid = entry.id

    resp = client.post(f"/journal/{eid}/edit", data={
        "content": "Updated content",
        "user_emotion": "Happy",
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app.app_context():
        updated = JournalEntry.query.get(eid)
        assert updated.content == "Updated content"
        assert updated.user_emotion == "Happy"


def test_delete_success(client, app):
    with app.app_context():
        entry = JournalEntry(user_id=app.test_user_id, content="To be deleted", user_emotion="Sad")
        db.session.add(entry)
        db.session.commit()
        eid = entry.id

    resp = client.post(f"/journal/{eid}/delete", data={}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        deleted = JournalEntry.query.get(eid)
        assert deleted is None
