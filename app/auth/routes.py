from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_login import login_user
from .forms import LoginForm, RegisterForm
from ..models import User
from ..extensions import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # search for the user in the database
        user = User.query.filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            # log the user in
            login_user(user)
            flash("Login sucessful :)")
            return redirect(url_for("main.home"))

        flash("Invalid username or password.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # search for an existing user in the database
        existing_user = User.query.filter(User.username == form.username.data).first()
        if existing_user:
            # show an error and return to the form page
            form.username.errors.append("Username already exists.")
            return render_template("auth/register.html", form=form)

        existing_email = User.query.filter(User.email == form.email.data).first()
        if existing_email:
            form.email.errors.append("Email already exists.")
            return render_template("auth/register.html", form=form)

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

        flash("Registration successful :)! Please log in.", "success")

        return redirect(url_for("auth.login"))
            

    return render_template("auth/register.html", form=form)
    
        
    



