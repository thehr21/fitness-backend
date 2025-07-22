from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import random
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from app.database import get_db
from app import models, schemas
from app.email_utils import send_reset_code  # ✅ Correct function name
from app.models import PasswordResetCode


#  Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_CODE_EXPIRE_MINUTES = 15  #  Reset code expires in 15 min

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter()

#  Generate a 6-digit reset code
def generate_reset_code():
    return str(random.randint(100000, 999999))

#  Hash Password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify Password
def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

#  Create Access Token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

#  User Registration
@router.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    new_user = models.User(
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        password=hashed_password,
        activity_level=user.activity_level, 
        goal=user.goal,
        current_weight=user.current_weight,
        target_weight=user.target_weight,
        gender=user.gender
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token({"sub": new_user.email}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer",  "activity_level": new_user.activity_level }

#  User Login
@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token({"sub": db_user.id}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {
        "access_token": access_token,
        "user_id": db_user.id,  # Ensure user_id is returned
        "activity_level": db_user.activity_level,  #  Ensure activity_level is returned
        "token_type": "bearer"
    }

#  Check if Email is Already Registered
class EmailCheckRequest(BaseModel):
    email: str

@router.post("/check-email")
def check_email(request: EmailCheckRequest, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return {"message": "Email is available"}

#  Forgot Password - Generate & Send Reset Code
class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Handles forgot password requests by generating and emailing a reset code."""
    
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_code = generate_reset_code()
    expiration_time = datetime.utcnow() + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES)

    
    db.query(models.PasswordResetCode).filter(models.PasswordResetCode.user_id == user.id).delete()

    
    new_reset_code = models.PasswordResetCode(user_id=user.id, code=reset_code, expires_at=expiration_time)
    db.add(new_reset_code)
    db.commit()

    await send_reset_code(db, user.email)  


    return {"message": "A password reset code has been sent to your email."}


class VerifyResetCodeRequest(BaseModel):
    email: str
    reset_code: str

@router.post("/verify-reset-code")
def verify_reset_code(request: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    """Verifies if the reset code is correct and not expired."""

    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    reset_entry = db.query(models.PasswordResetCode).filter(models.PasswordResetCode.user_id == user.id).first()

    if not reset_entry or reset_entry.reset_code != request.reset_code:
        raise HTTPException(status_code=400, detail="Invalid reset code")

    if reset_entry.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset code has expired")

    return {"message": "Reset code is valid"}

#  Reset Password
class ResetPasswordRequest(BaseModel):
    email: str
    reset_code: str
    new_password: str

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Handles resetting the password after verifying the reset code."""

    print(f"📌 DEBUG: Received Reset Request for Email={request.email} with Code={request.reset_code}")

    # Fetch the reset code entry from the database
    reset_entry = db.query(models.PasswordResetCode).filter(
        models.PasswordResetCode.user_id == models.User.id,
        models.User.email == request.email
    ).first()

    if not reset_entry:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")

    print(f" DEBUG: Found reset entry: {reset_entry}")

    # Check if reset code matches
    if reset_entry.code != request.reset_code:  # ✅ Change reset_code to code
        raise HTTPException(status_code=400, detail="Incorrect reset code")

    #  Check if reset code has expired
    if datetime.utcnow() > reset_entry.expires_at:
        raise HTTPException(status_code=400, detail="Reset code has expired")

    #  Find the user and update their password
    user = db.query(models.User).filter(models.User.id == reset_entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    #  Hash new password
    hashed_password = pwd_context.hash(request.new_password)
    user.password = hashed_password
    db.commit()

    #  Delete the reset code after successful password reset
    db.delete(reset_entry)
    db.commit()

    print(" DEBUG: Password reset successful!")
    return {"message": "Password reset successful"}

@router.get("/user-goal")
def get_user_goal(user_id: int, db: Session = Depends(get_db)):
    """
    Fetches the fitness goal of a user based on their ID.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"goal": user.goal}
