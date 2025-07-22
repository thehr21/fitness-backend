from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


# ------------------ USER SCHEMA ------------------
class UserPublic(BaseModel):
    """Schema to return public user information (without password)."""
    id: int
    full_name: str
    username: str
    profile_picture: Optional[str] = None  # Can be None if user has no profile picture

    class Config:
        from_attributes = True


# ------------------ AUTH SCHEMAS ------------------
class UserCreate(BaseModel):
    """Schema for user registration."""
    full_name: str
    username: str
    email: EmailStr
    password: str
    goal: str
    current_weight: float
    target_weight: float
    gender: str
    activity_level: str


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str
    activity_level: str


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""
    token: str
    new_password: str


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile (full name, username)."""
    full_name: str
    username: str
    current_weight: float

# ------------------ MEAL LOGGING SCHEMAS ------------------
class MealResponse(BaseModel):
    """Schema for returning logged meals."""
    id: int
    spoonacular_id: int
    food_item: str
    calories: int
    protein: float
    carbs: float
    fats: float
    goal: str

    class Config:
        from_attributes = True  #  Fixes "orm_mode" warning in Pydantic v2


class LoggedMealRequest(BaseModel):
    """Schema for logging a new meal."""
    user_id: int
    food_item: str
    calories: int
    protein: float
    carbs: float
    fats: float


class LoggedMealResponse(LoggedMealRequest):
    """Schema for returning a logged meal with timestamp."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# ------------------ POST SCHEMAS ------------------
class PostBase(BaseModel):
    """Base schema for a post."""
    content: str
    media_url: Optional[str] = None  # Optional Image/Video


class PostCreate(PostBase):
    """Schema for creating a post."""
    user_id: int  # Required for post creation


class PostResponse(PostBase):
    """Schema for returning a post, now includes user details."""
    id: int
    user: UserPublic  #  Includes user details (full name, username, profile picture)
    likes: int
    date_posted: datetime

    class Config:
        from_attributes = True  #  Fix for Pydantic ORM Mode


# ------------------ COMMENT SCHEMAS ------------------
class CommentBase(BaseModel):
    """Base schema for a comment."""
    content: str


class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    post_id: int
    user_id: int


class CommentResponse(CommentBase):
    """Schema for returning a comment, now includes user details."""
    id: int
    post_id: int
    user: UserPublic  #  Includes user details
    date_posted: datetime

    class Config:
        from_attributes = True


# ------------------ PASSWORD RESET SCHEMA ------------------
class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    """Schema for verifying reset code."""
    email: EmailStr
    reset_code: str


class PasswordResetConfirmRequest(BaseModel):
    """Schema for confirming password reset."""
    email: EmailStr
    reset_code: str
    new_password: str

    # ------------------ WORKOUT LOG SCHEMAS ------------------

class WorkoutLogRequest(BaseModel):
    """Schema for logging a new workout."""
    user_id: int
    workout_name: str
    muscle_group: str
    equipment: str

class WorkoutLogResponse(WorkoutLogRequest):
    """Schema for returning a logged workout."""
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True  # Fix for Pydantic ORM Mode
