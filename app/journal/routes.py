from flask import Blueprint, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy import select

from ..extensions import db
from ..models import JournalEntry
from .forms import JournalEntryForm

journal_bp = Blueprint("journal", __name__, url_prefix="/journal")

@journal_bp.route("/", methods=["GET"])
@login_required
def journal_list():
    stmt = select(JournalEntry).filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc())
    entries = db.session.scalars(stmt).all()
    # Minimal HTML list until templates added
    items = "".join(f"<li>{e.created_at} — {e.user_emotion}: {e.content[:200]}</li>" for e in entries)
    return f"<h1>Your journal entries ({len(entries)})</h1><ul>{items}</ul>", 200

@journal_bp.route("/new", methods=["GET", "POST"])
@login_required
def journal_create():
    form = JournalEntryForm()
    if form.validate_on_submit():
        entry = JournalEntry(
            user_id=current_user.id,
            content=form.content.data,
            user_emotion=form.user_emotion.data,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Journal entry created.", "success")
        return redirect(url_for("journal.journal_list"))
    # For GET or invalid POST show simple instructions (templates to be added in sub-issue 7)
    return (
        "<h1>New Journal Entry</h1>"
        "<p>Submit via POST with fields `content` and `user_emotion` (CSRF token required).</p>",
        200,
    )


def _get_owned_entry_or_404(entry_id: int) -> JournalEntry:
    """Return the JournalEntry if it belongs to current_user, else abort 404."""
    stmt = select(JournalEntry).filter_by(id=entry_id, user_id=current_user.id)
    entry = db.session.scalars(stmt).one_or_none()
    if entry is None:
        abort(404)
    return entry


@journal_bp.route("/<int:entry_id>", methods=["GET"])
@login_required
def journal_detail(entry_id: int):
    entry = _get_owned_entry_or_404(entry_id)
    # Minimal plaintext/detail until templates are added
    return f"<h1>Entry {entry.id}</h1><p>{entry.created_at} — {entry.user_emotion}</p><div>{entry.content}</div>", 200
