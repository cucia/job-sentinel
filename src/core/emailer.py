import os
import smtplib
from email.message import EmailMessage


def _get_env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def send_resume(
    to_address: str,
    subject: str,
    body: str,
    resume_path: str | None = None,
) -> None:
    gmail_address = _get_env("GMAIL_ADDRESS")
    gmail_app_password = _get_env("GMAIL_APP_PASSWORD")
    from_name = _get_env("MAIL_FROM_NAME", gmail_address)

    if not gmail_address or not gmail_app_password:
        raise RuntimeError("Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD in environment.")

    msg = EmailMessage()
    msg["From"] = f"{from_name} <{gmail_address}>"
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(body)

    if resume_path and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(resume_path),
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(msg)
