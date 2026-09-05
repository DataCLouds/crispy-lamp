from datetime import datetime
from typing import Any
import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Base, JournalEntry, User


@pytest.fixture
def engine():
    """Create a fresh in-memory SQLite database engine for each test with foreign keys enabled."""
    db_engine = create_engine("sqlite:///:memory:")

    # SQLite does not enforce foreign keys by default; enable foreign key support
    @event.listens_for(db_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(db_engine)
    yield db_engine
    Base.metadata.drop_all(db_engine)
    db_engine.dispose()


@pytest.fixture
def session(engine):
    """Provide a transactional SQLAlchemy session per test."""
    with Session(engine) as db_session:
        yield db_session


# ---------------------------------------------------------------------------
# Schema and Column Definitions
# ---------------------------------------------------------------------------

def test_database_schema_and_column_specifications(engine):
    """Verify tables, columns, primary keys, and nullability match model definitions."""
    inspector = inspect(engine)

    assert inspector.has_table("users"), "Table 'users' should exist."
    assert inspector.has_table("journal_entries"), "Table 'journal_entries' should exist."

    # Validate primary key constraints
    assert inspector.get_pk_constraint("users")["constrained_columns"] == ["id"]
    assert inspector.get_pk_constraint("journal_entries")["constrained_columns"] == ["id"]

    # Validate User table columns
    user_columns = {col["name"]: col for col in inspector.get_columns("users")}
    assert "id" in user_columns
    assert "username" in user_columns and not user_columns["username"]["nullable"]
    assert "email" in user_columns and not user_columns["email"]["nullable"]
    assert "first_name" in user_columns and user_columns["first_name"]["nullable"]
    assert "password_hash" in user_columns and not user_columns["password_hash"]["nullable"]
    assert "created_at" in user_columns and not user_columns["created_at"]["nullable"]

    # Validate JournalEntry table columns
    entry_columns = {col["name"]: col for col in inspector.get_columns("journal_entries")}
    assert "id" in entry_columns
    assert "user_id" in entry_columns and not entry_columns["user_id"]["nullable"]
    assert "content" in entry_columns and not entry_columns["content"]["nullable"]
    assert "user_emotion" in entry_columns and not entry_columns["user_emotion"]["nullable"]
    assert "created_at" in entry_columns and not entry_columns["created_at"]["nullable"]
    assert "updated_at" in entry_columns and entry_columns["updated_at"]["nullable"]


# ---------------------------------------------------------------------------
# User Model Tests: Basic CRUD, Nullability, Uniqueness, and Password Hashing
# ---------------------------------------------------------------------------

def test_create_user_with_optional_fields(session):
    """Test user creation with all fields, including optional first_name."""
    user = User(username="alice", email="alice@example.com", first_name="Alice")
    user.set_password("SecurePass#2026")
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.first_name == "Alice"
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
    assert user.check_password("SecurePass#2026") is True
    assert user.entries == []


def test_create_user_without_first_name(session):
    """Corner case: first_name is nullable and should accept None."""
    user = User(username="bob", email="bob@example.com", first_name=None)
    user.set_password("B0bPassword!")
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.first_name is None


def test_user_unique_username_constraint(session):
    """Corner case: Duplicate usernames must be rejected by unique constraint."""
    user1 = User(username="duplicate_user", email="user1@example.com")
    user1.set_password("pass12345")
    session.add(user1)
    session.commit()

    user2 = User(username="duplicate_user", email="user2@example.com")
    user2.set_password("pass67890")
    session.add(user2)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_user_unique_email_constraint(session):
    """Corner case: Duplicate email addresses must be rejected by unique constraint."""
    user1 = User(username="unique_user1", email="shared@example.com")
    user1.set_password("pass12345")
    session.add(user1)
    session.commit()

    user2 = User(username="unique_user2", email="shared@example.com")
    user2.set_password("pass67890")
    session.add(user2)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize("missing_field,user_kwargs", [
    ("username", {"email": "no_user@example.com", "password_hash": "hash"}),
    ("email", {"username": "no_email_user", "password_hash": "hash"}),
    ("password_hash", {"username": "no_pw_user", "email": "no_pw@example.com"}),
])
def test_user_not_null_constraints(session, missing_field, user_kwargs):
    """Corner case: Null values for mandatory columns must raise IntegrityError."""
    user = User(**user_kwargs)
    session.add(user)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_password_hashing_security_and_edge_cases(session):
    """Verify password hashing mechanics: plain text is not stored, verification, update."""
    user = User(username="charlie", email="charlie@example.com")
    plain_password = "MyComplexPassword#123"
    user.set_password(plain_password)

    # Password hash should never equal plain password
    assert user.password_hash != plain_password
    assert len(user.password_hash) > 20
    assert user.check_password(plain_password) is True
    assert user.check_password("wrong_password") is False
    assert user.check_password(plain_password.lower()) is False  # Case sensitivity check

    # Edge case: updating password with a new one
    new_password = "UpdatedNewPassword#456"
    user.set_password(new_password)
    assert user.check_password(new_password) is True
    assert user.check_password(plain_password) is False


# ---------------------------------------------------------------------------
# JournalEntry Model Tests: FK, Not-Null, Cascades, Timestamps, Relationships
# ---------------------------------------------------------------------------

def test_journal_entry_creation_and_relationship(session):
    """Test standard JournalEntry creation and bidirectional relationship."""
    user = User(username="dave", email="dave@example.com")
    user.set_password("password123")
    session.add(user)
    session.commit()

    entry = JournalEntry(user_id=user.id, content="Had a very productive day coding.", user_emotion="Happy")
    session.add(entry)
    session.commit()
    session.refresh(entry)
    session.refresh(user)

    assert entry.id is not None
    assert entry.user_id == user.id
    assert entry.content == "Had a very productive day coding."
    assert entry.user_emotion == "Happy"
    assert entry.created_at is not None
    assert isinstance(entry.created_at, datetime)
    assert entry.updated_at is None
    assert entry.user == user
    assert len(user.entries) == 1
    assert user.entries[0] == entry


def test_journal_entry_append_to_relationship(session):
    """Test creating entries via relationship collection directly."""
    user = User(username="eva", email="eva@example.com")
    user.set_password("password123")
    session.add(user)
    session.commit()

    entry1 = JournalEntry(content="Morning reflection", user_emotion="Neutral")
    entry2 = JournalEntry(content="Evening summary", user_emotion="Happy")
    user.entries.extend([entry1, entry2])
    session.commit()
    session.refresh(user)

    assert len(user.entries) == 2
    assert entry1.user_id == user.id
    assert entry2.user_id == user.id


def test_foreign_key_constraint_invalid_user_id(session):
    """Corner case: Inserting JournalEntry with non-existent user_id must fail."""
    non_existent_user_id = 99999
    entry = JournalEntry(
        user_id=non_existent_user_id,
        content="Entry without parent user",
        user_emotion="Sad",
    )
    session.add(entry)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


@pytest.mark.parametrize("missing_field,entry_kwargs", [
    ("content", {"user_emotion": "Neutral"}),
    ("user_emotion", {"content": "Some thoughts"}),
    ("user_id", {"content": "Some thoughts", "user_emotion": "Neutral"}),
])
def test_journal_entry_not_null_constraints(session, missing_field, entry_kwargs: dict[str, Any]):
    """Corner case: Mandatory JournalEntry fields cannot be null."""
    user = User(username="frank", email="frank@example.com")
    user.set_password("password123")
    session.add(user)
    session.commit()

    kwargs = dict(entry_kwargs)
    if "user_id" not in kwargs and missing_field != "user_id":
        kwargs["user_id"] = user.id

    entry = JournalEntry(**kwargs)
    session.add(entry)

    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_cascade_delete_user_deletes_entries(session):
    """Corner case: Deleting a User must cascade delete all associated JournalEntries."""
    user = User(username="grace", email="grace@example.com")
    user.set_password("password123")
    session.add(user)
    session.commit()

    entry1 = JournalEntry(user_id=user.id, content="Note 1", user_emotion="Neutral")
    entry2 = JournalEntry(user_id=user.id, content="Note 2", user_emotion="Happy")
    session.add_all([entry1, entry2])
    session.commit()

    entry_ids = [entry1.id, entry2.id]
    assert len(entry_ids) == 2

    # Delete the user
    session.delete(user)
    session.commit()

    # Verify user is deleted
    assert session.get(User, user.id) is None

    # Verify all related journal entries are cascade-deleted
    for eid in entry_ids:
        assert session.get(JournalEntry, eid) is None

    remaining_entries = session.scalars(select(JournalEntry)).all()
    assert len(remaining_entries) == 0


def test_orphan_removal_on_entries_collection(session):
    """Corner case: Removing an entry from user.entries deletes the orphaned record."""
    user = User(username="isabel", email="isabel@example.com")
    user.set_password("password123")
    entry1 = JournalEntry(content="Entry to keep", user_emotion="Happy")
    entry2 = JournalEntry(content="Entry to remove", user_emotion="Neutral")
    user.entries.extend([entry1, entry2])
    session.add(user)
    session.commit()
    session.refresh(user)

    entry2_id = entry2.id
    assert len(user.entries) == 2

    # Remove entry2 from user's relationship collection (delete-orphan cascade)
    user.entries.remove(entry2)
    session.commit()

    assert len(user.entries) == 1
    assert session.get(JournalEntry, entry2_id) is None


def test_journal_entry_updated_at_timestamp(session):
    """Verify updated_at is None on creation and populated upon modification."""
    user = User(username="helen", email="helen@example.com")
    user.set_password("password123")
    session.add(user)
    session.commit()

    entry = JournalEntry(user_id=user.id, content="Original thought", user_emotion="Neutral")
    session.add(entry)
    session.commit()
    session.refresh(entry)

    assert entry.updated_at is None
    original_created_at = entry.created_at

    # Update the entry
    entry.content = "Revised thought after reflection"
    session.commit()
    session.refresh(entry)

    assert entry.content == "Revised thought after reflection"
    assert entry.updated_at is not None
    assert isinstance(entry.updated_at, datetime)
    assert entry.created_at == original_created_at
