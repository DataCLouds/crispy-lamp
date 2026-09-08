from flask import Blueprint, request, render_template, flash, redirect, url_for
from .forms import LoginForm, RegisterForm
from ..models import User
from ..extensions import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template("auth/login.html", form=form)
    if request.method == "POST":
        return "Login POST works Hooray :)", 200


"""
if form.validate_on_submit():
    search for an existing user in the dataabase
    if username already exists:
        show an error message and return to the form page
    if email already exists:
        show an error message and return to the form page

    create a new User using the submitted non-password fields

    hash the submitted password with set_password()

    add the user to the database

    commit the transaction

    flash success message
    
    redirect to login

render registration template
"""
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # search for an existing user in the database
        existing_user = User.query.filter(User.username == form.username.data).first()
        if existing_user:
            # show an error and return to the form page
            form.username.errors.append("Username already exists.")
            return render_template("auth/register.html", form=form, error="Username already exists.")

        existing_email = User.query.filter(User.email == form.email.data).first()
        if existing_email:
            form.email.errors.append("Email already exists.")
            return render_template("auth/register.html", form=form, error="Email already exists.")

        #  create a new user using the submitted non-password fields
        new_user = User(
            username = form.username.data,
            email = form.email.data,
            first_name = form.first_name.data,
        )

        # hash the submitted password
        new_user.set_password(form.password.data)

        # add the user to the database
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")

        return redirect(url_for("auth.login"))
            

    return render_template("auth/register.html", form=form)
    
        
    



