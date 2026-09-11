from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy import select

from app import create_app
from app.extensions import db
from app.models import JournalEntry, User


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
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
    with client.session_transaction() as sess:
        sess["_user_id"] = str(app.test_user_id)
        sess["_fresh"] = True
    return client


def test_get_new_entry_form_renders_successfully(client):
    response = client.get("/journal/new")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "New Journal Entry" in html
    assert "How are you feeling?" in html


def test_create_journal_entry_success(client, app):
    response = client.post(
        "/journal/new",
        data={
            "content": "Today was a productive day building features.",
            "user_emotion": "Happy",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Journal entry created." in response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.user_id == app.test_user_id)
        entries = db.session.scalars(stmt).all()
        assert len(entries) == 1
        assert entries[0].content == "Today was a productive day building features."
        assert entries[0].user_emotion == "Happy"
        assert entries[0].created_at is not None
        assert entries[0].updated_at is None


def test_list_journal_entries_displays_only_owner_entries(client, app):
    with app.app_context():
        other_user = User(username="other_user", email="other@example.com")
        other_user.set_password("secret123")
        db.session.add(other_user)
        db.session.commit()

        other_entry = JournalEntry(
            user_id=other_user.id,
            content="Other user private thoughts",
            user_emotion="Sad",
        )
        my_entry = JournalEntry(
            user_id=app.test_user_id,
            content="My personal reflection",
            user_emotion="Happy",
        )
        db.session.add_all([other_entry, my_entry])
        db.session.commit()

    response = client.get("/journal/")
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    assert "My personal reflection" in content
    assert "Other user private thoughts" not in content


def test_list_journal_entries_default_ordering_newest_first(client, app):
    now = datetime.now(UTC)
    with app.app_context():
        older_entry = JournalEntry(
            user_id=app.test_user_id,
            content="Older entry recorded earlier",
            user_emotion="Neutral",
            created_at=now - timedelta(days=2),
        )
        newer_entry = JournalEntry(
            user_id=app.test_user_id,
            content="Newer entry recorded today",
            user_emotion="Happy",
            created_at=now,
        )
        db.session.add_all([older_entry, newer_entry])
        db.session.commit()

    response = client.get("/journal/")
    assert response.status_code == 200
    content = response.get_data(as_text=True)
    idx_newer = content.find("Newer entry recorded today")
    idx_older = content.find("Older entry recorded earlier")
    assert idx_newer != -1 and idx_older != -1
    assert idx_newer < idx_older


def test_list_journal_entries_pagination(client, app):
    now = datetime.now(UTC)
    with app.app_context():
        entries = [
            JournalEntry(
                user_id=app.test_user_id,
                content=f"Paginated entry #{i}",
                user_emotion="Happy",
                created_at=now + timedelta(minutes=i),
            )
            for i in range(1, 16)
        ]
        db.session.add_all(entries)
        db.session.commit()

    response_page1 = client.get("/journal/?page=1&per_page=5")
    assert response_page1.status_code == 200
    page1_html = response_page1.get_data(as_text=True)
    assert "Page 1 of 3" in page1_html
    assert "Paginated entry #15" in page1_html
    assert "Next" in page1_html

    response_page2 = client.get("/journal/?page=2&per_page=5")
    assert response_page2.status_code == 200
    page2_html = response_page2.get_data(as_text=True)
    assert "Page 2 of 3" in page2_html
    assert "Previous" in page2_html


def test_list_journal_entries_filter_by_emotion(client, app):
    with app.app_context():
        e_happy = JournalEntry(
            user_id=app.test_user_id,
            content="Happy entry",
            user_emotion="Happy",
        )
        e_sad = JournalEntry(
            user_id=app.test_user_id,
            content="Sad entry",
            user_emotion="Sad",
        )
        db.session.add_all([e_happy, e_sad])
        db.session.commit()

    response = client.get("/journal/?emotion=Happy")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Happy entry" in html
    assert "Sad entry" not in html


def test_list_journal_entries_filter_by_search_keyword(client, app):
    with app.app_context():
        e1 = JournalEntry(
            user_id=app.test_user_id,
            content="Working on python backend algorithms",
            user_emotion="Happy",
        )
        e2 = JournalEntry(
            user_id=app.test_user_id,
            content="Taking a stroll in the park",
            user_emotion="Neutral",
        )
        db.session.add_all([e1, e2])
        db.session.commit()

    response = client.get("/journal/?search=python")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Working on python backend algorithms" in html
    assert "Taking a stroll in the park" not in html


def test_list_journal_entries_filter_by_date_range(client, app):
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)
    two_days_ago = today - timedelta(days=2)

    with app.app_context():
        e_old = JournalEntry(
            user_id=app.test_user_id,
            content="Old entry 2 days ago",
            user_emotion="Neutral",
            created_at=datetime(two_days_ago.year, two_days_ago.month, two_days_ago.day, 12, 0, 0, tzinfo=UTC),
        )
        e_yesterday = JournalEntry(
            user_id=app.test_user_id,
            content="Entry from yesterday",
            user_emotion="Happy",
            created_at=datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0, 0, tzinfo=UTC),
        )
        e_today = JournalEntry(
            user_id=app.test_user_id,
            content="Entry from today",
            user_emotion="Stressed",
            created_at=datetime(today.year, today.month, today.day, 12, 0, 0, tzinfo=UTC),
        )
        db.session.add_all([e_old, e_yesterday, e_today])
        db.session.commit()

    response = client.get(
        f"/journal/?start_date={yesterday.isoformat()}&end_date={yesterday.isoformat()}"
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Entry from yesterday" in html
    assert "Old entry 2 days ago" not in html
    assert "Entry from today" not in html


def test_get_journal_entry_detail_success(client, app):
    with app.app_context():
        entry = JournalEntry(
            user_id=app.test_user_id,
            content="Deep reflection details",
            user_emotion="Neutral",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    response = client.get(f"/journal/{entry_id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f"Entry {entry_id}" in html
    assert "Deep reflection details" in html
    assert "Neutral" in html


def test_get_edit_journal_entry_form_renders_successfully(client, app):
    with app.app_context():
        entry = JournalEntry(
            user_id=app.test_user_id,
            content="Content before editing",
            user_emotion="Sad",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    response = client.get(f"/journal/{entry_id}/edit")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f"Edit Entry {entry_id}" in html
    assert "Content before editing" in html


def test_edit_journal_entry_updates_content_and_timestamp(client, app):
    with app.app_context():
        entry = JournalEntry(
            user_id=app.test_user_id,
            content="Original content",
            user_emotion="Neutral",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    response = client.post(
        f"/journal/{entry_id}/edit",
        data={
            "content": "Updated reflected content",
            "user_emotion": "Happy",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Journal entry updated." in response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
        updated = db.session.scalars(stmt).one()
        assert updated.content == "Updated reflected content"
        assert updated.user_emotion == "Happy"
        assert updated.updated_at is not None


def test_delete_journal_entry_success(client, app):
    with app.app_context():
        entry = JournalEntry(
            user_id=app.test_user_id,
            content="Entry to be deleted permanently",
            user_emotion="Angry",
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    response = client.post(f"/journal/{entry_id}/delete", data={}, follow_redirects=True)
    assert response.status_code == 200
    assert "Journal entry deleted." in response.get_data(as_text=True)

    with app.app_context():
        stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
        deleted = db.session.scalars(stmt).one_or_none()
        assert deleted is None
