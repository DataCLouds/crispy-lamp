from datetime import UTC, datetime
from flask import Blueprint, request, redirect, url_for, flash, abort, render_template
from flask_login import login_required, current_user
from sqlalchemy import select

from ..extensions import db
from ..models import JournalEntry
from .forms import JournalEntryForm, DeleteForm, EMOTION_CHOICES

journal_bp = Blueprint("journal", __name__, url_prefix="/journal")


@journal_bp.route("/", methods=["GET"])
@login_required
def journal_list():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    emotion = request.args.get("emotion", type=str, default="").strip()
    search = request.args.get("search", type=str, default="").strip()
    start_date_str = request.args.get("start_date", type=str, default="").strip()
    end_date_str = request.args.get("end_date", type=str, default="").strip()

    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    elif per_page > 100:
        per_page = 100

    stmt = select(JournalEntry).where(JournalEntry.user_id == current_user.id)

    if emotion:
        stmt = stmt.where(JournalEntry.user_emotion == emotion)

    if search:
        stmt = stmt.where(JournalEntry.content.ilike(f"%{search}%"))

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
            stmt = stmt.where(JournalEntry.created_at >= start_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=UTC
            )
            stmt = stmt.where(JournalEntry.created_at <= end_date)
        except ValueError:
            pass

    stmt = stmt.order_by(JournalEntry.created_at.desc())

    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    entries = pagination.items
    delete_form = DeleteForm()

    return render_template(
        "journal/list.html",
        entries=entries,
        pagination=pagination,
        delete_form=delete_form,
        emotion_choices=EMOTION_CHOICES,
        current_emotion=emotion,
        current_search=search,
        current_start_date=start_date_str,
        current_end_date=end_date_str,
    )


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
    stmt = select(JournalEntry).where(JournalEntry.id == entry_id, JournalEntry.user_id == current_user.id)
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
