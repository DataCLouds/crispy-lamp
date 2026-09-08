from flask import Blueprint
from flask_login import login_required
from .forms import JournalEntryForm

journal_bp = Blueprint("journal", __name__)

@journal_bp.route("/journal",methods=["GET"])
@login_required
def journal_list():
    form = JournalEntryForm()
    if form.validate_on_submit():
        # handle form submission
        pass
    return "Journal entries",200
