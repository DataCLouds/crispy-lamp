from flask import Blueprint, request, redirect, url_for, flash, abort, render_template
from flask_login import login_required, current_user
from sqlalchemy import select

from ..extensions import db
from ..models import JournalEntry
from .forms import JournalEntryForm, DeleteForm

journal_bp = Blueprint("journal", __name__, url_prefix="/journal")

@journal_bp.route("/", methods=["GET"])
@login_required
def journal_list():
    stmt = select(JournalEntry).filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc())
    entries = db.session.scalars(stmt).all()
    delete_form = DeleteForm()
    return render_template("journal/list.html", entries=entries, delete_form=delete_form)


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
    return render_template("journal/new.html", form=form)


def _get_owned_entry_or_404(entry_id: int) -> JournalEntry:
    stmt = select(JournalEntry).filter_by(id=entry_id, user_id=current_user.id)
    entry = db.session.scalars(stmt).one_or_none()
    if entry is None:
        abort(404)
    return entry


@journal_bp.route("/<int:entry_id>", methods=["GET"])
@login_required
def journal_detail(entry_id: int):
    entry = _get_owned_entry_or_404(entry_id)
    delete_form = DeleteForm()
    return render_template("journal/detail.html", entry=entry, delete_form=delete_form)


@journal_bp.route("/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def journal_edit(entry_id: int):
    entry = _get_owned_entry_or_404(entry_id)
    form = JournalEntryForm(obj=entry)

    if form.validate_on_submit():
        entry.content = form.content.data
        entry.user_emotion = form.user_emotion.data
        # SQLAlchemy will manage updated_at on update if configured; persist changes
        db.session.add(entry)
        db.session.commit()
        flash("Journal entry updated.", "success")
        return redirect(url_for("journal.journal_detail", entry_id=entry.id))

    return render_template("journal/edit.html", form=form, entry=entry)


@journal_bp.route("/<int:entry_id>/delete", methods=["POST"])
@login_required
def journal_delete(entry_id: int):
    form = DeleteForm()
    if not form.validate_on_submit():
        abort(400)
    entry = _get_owned_entry_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("Journal entry deleted.", "success")
    return redirect(url_for("journal.journal_list"))
