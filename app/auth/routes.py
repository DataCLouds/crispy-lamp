from flask import Blueprint, request

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return "Login GET works YAY :D", 200
    return "Login POST works Hooray :)", 200

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return "Register GET works YAY :D", 200
    return "Register POST woorks HOORAY :)", 200
    



