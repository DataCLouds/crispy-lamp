from flask import Blueprint
from flask_login import login_required

journal_bp = Blueprint("journal", __name__)

@journal_bp.route("/journal",methods=["GET"])
@login_required
def journal_list():
    return "Journal entries",200
