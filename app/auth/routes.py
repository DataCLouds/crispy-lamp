from flask import Blueprint, request, render_template
from .forms import LoginForm, RegisterForm

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template("auth/login.html", form=form)
    if request.method == "POST":
        return "Login POST works Hooray :)", 200

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if request.method == "GET":
        return render_template("auth/register.html", form=form)
    if request.method == "POST":
        return "Register POST woorks HOORAY :)", 200
    



