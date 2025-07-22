import random
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from app.models import User, PasswordResetCode

# Load environment variables
load_dotenv()

# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    USE_CREDENTIALS=True
)

def generate_reset_code():
    """Generates a 6-digit numeric reset code."""
    return str(random.randint(100000, 999999))

async def send_reset_code(db: Session, email: str):
    """Sends a reset code to the user's email and stores it in the database."""
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")

    reset_code = generate_reset_code()
    expiration_time = datetime.utcnow() + timedelta(minutes=15)  # ✅ Code expires in 15 minutes

    # Remove any existing reset code for the user
    db.query(PasswordResetCode).filter(PasswordResetCode.user_id == user.id).delete()
    
    # Store the new reset code in the database
    reset_entry = PasswordResetCode(user_id=user.id, code=reset_code, expires_at=expiration_time)
    db.add(reset_entry)
    db.commit()

    # Create email message
    message = MessageSchema(
        subject="Your Password Reset Code",
        recipients=[email],
        body=f"Your password reset code is: {reset_code}\n\nThis code will expire in 15 minutes.",
        subtype="plain"
    )

    fm = FastMail(conf)

    try:
        await fm.send_message(message)
        print(f" Reset code {reset_code} sent to {email}")
    except Exception as e:
        print(f" Error sending reset email: {e}")
