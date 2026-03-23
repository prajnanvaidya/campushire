from flask import Blueprint, render_template, request, url_for, flash, redirect
from flask_mail import Message
from app import mail

home_bp=Blueprint("home", __name__)

@home_bp.route("/")
def house():
    return render_template("home.html", role="guest")

@home_bp.route("/contact", methods=["POST"])
def contact():

    email = request.form.get("email")
    message = request.form.get("message")

    msg = Message(
        subject="CampusHire Contact Form",
        recipients=["prajnan247@gmail.com"]
    )

    msg.body = f"""
    Message from: {email}

    {message}
    """

    mail.send(msg)

    flash("Your message has been sent successfully!", "success")

    return redirect(url_for("home.house"))