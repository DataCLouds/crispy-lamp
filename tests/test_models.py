from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.models import Base, JournalEntry, User


def test_database_tables_are_created():
    engine = create_engine("sqlite://")

    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    assert inspector.has_table("users")
    assert inspector.has_table("journal_entries")


def test_user_journal_relationship_and_password_hashing():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(username="alice", email="alice@example.com", first_name="Alice")
        user.set_password("secret123")
        session.add(user)
        session.commit()
        session.refresh(user)

        entry = JournalEntry(user_id=user.id, content="Today felt productive.", user_emotion="happy")
        session.add(entry)
        session.commit()
        session.refresh(entry)

        assert user.check_password("secret123") is True
        assert user.check_password("wrongpassword") is False
        assert entry.user_id == user.id
        assert entry.user.username == "alice"
        assert user.entries[0].content == "Today felt productive."


def test_first_name_can_be_none():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(username="bob", email="bob@example.com", first_name=None)
        user.set_password("secret456")
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.first_name is None
        assert user.check_password("secret456") is True
