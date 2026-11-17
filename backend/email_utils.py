
import smtplib
import ssl
from email.message import EmailMessage

from flask import current_app


def send_email(to_email, subject, body, html=False):

    # Read email settings from Flask configuration
    host = current_app.config["SMTP_HOST"]
    port = current_app.config["SMTP_PORT"]
    username = current_app.config["SMTP_USERNAME"]
    password = current_app.config["SMTP_PASSWORD"]
    sender = current_app.config["SMTP_SENDER"] or username

    # Check whether email is configured
    if not username or not password or not sender:
        raise RuntimeError(
            "SMTP email settings are not configured."
        )

    # Create email message
    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject

    if html:
        message.set_content(
            "Please view this email using an HTML-compatible email client."
        )
        message.add_alternative(body, subtype="html")
    else:
        message.set_content(body)

    # Connect securely to the email server
    context = ssl.create_default_context()

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(username, password)
        server.send_message(message)

    return True
