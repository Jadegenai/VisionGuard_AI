"""Email notification for safety violations."""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime


def send_violation_email(
    violation_type: str,
    timestamp: datetime,
    location: str,
    image_path: str = None,
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_password: str = "",
    sender_email: str = "",
    recipient_emails: str = "",
):
    """Send an email alert for a safety violation with the snapshot attached.

    Args:
        violation_type: Type of violation (e.g. 'helmet_missing', 'glasses_missing').
        timestamp: When the violation occurred.
        location: Where the violation occurred.
        image_path: Path to the violation snapshot image.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        smtp_user: SMTP login username.
        smtp_password: SMTP login password.
        sender_email: Sender email address.
        recipient_emails: Comma-separated recipient email addresses.
    """
    if not smtp_host or not recipient_emails:
        print(f"[EMAIL] Skipped – SMTP not configured. Violation: {violation_type} at {timestamp}")
        return False

    recipients = [e.strip() for e in recipient_emails.split(",") if e.strip()]
    if not recipients:
        return False

    readable_type = violation_type.replace("_", " ").title()
    time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Safety Violation Alert – {readable_type} at {location}"

    body = (
        f"Safety Compliance Violation Detected\n"
        f"{'=' * 45}\n\n"
        f"Time:      {time_str}\n"
        f"Location:  {location}\n"
        f"Violation: {readable_type}\n\n"
        f"A safety compliance violation has been detected in the {location}. "
        f"Please review the attached snapshot and take appropriate action.\n\n"
        f"– VisionGuard AI Safety Monitoring System"
    )

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    if image_path and os.path.isfile(image_path):
        with open(image_path, "rb") as img_file:
            img = MIMEImage(img_file.read(), name=os.path.basename(image_path))
            img.add_header(
                "Content-Disposition", "attachment",
                filename=os.path.basename(image_path),
            )
            msg.attach(img)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print(f"[EMAIL] Sent violation alert: {readable_type} at {time_str}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False
