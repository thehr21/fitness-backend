from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.database import Base

# ------------------ USERS TABLE ------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)  
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    activity_level = Column(String, nullable=False)
    goal = Column(String, nullable=False)  # "muscle gain", "weight loss", "maintenance"
    current_weight = Column(Float, nullable=False)
    target_weight = Column(Float, nullable=False)
    gender = Column(String, nullable=False)  # "Male", "Female", "Other"
    profile_picture = Column(String, nullable=True) 

    # Relationships
    workouts = relationship("Workout", back_populates="user")
    meals = relationship("Meal", back_populates="user")
    posts = relationship("Post", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("Badge", back_populates="user", cascade="all, delete-orphan")
    streaks = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    reset_codes = relationship("PasswordResetCode", back_populates="user", cascade="all, delete-orphan")
    logged_meals = relationship("LoggedMeal", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    workout_logs = relationship("WorkoutLog", back_populates="user", cascade="all, delete-orphan")
# ------------------ PASSWORD RESET CODES TABLE ------------------
#  Reset Code Model
class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)  # 6-digit reset code
    expires_at = Column(DateTime, nullable=False)  # Expiration time

    user = relationship("User", back_populates="reset_codes")


User.reset_codes = relationship("PasswordResetCode", back_populates="user")

# ------------------ WORKOUTS TABLE ------------------
class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String, nullable=False)  # Example: "Cardio", "Strength Training"
    duration = Column(Integer, nullable=False)  # Duration in minutes
    date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workouts")

# ------------------ MEALS TABLE ------------------
class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_item = Column(String, nullable=False)
    image = Column(String, nullable=True)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)  # Protein in grams
    carbs = Column(Float, nullable=False)    # Carbs in grams
    fats = Column(Float, nullable=False)     # Fats in grams
    goal = Column(String, nullable=False)    # Weight Loss, Muscle Gain, Maintenance
    date = Column(DateTime, default=datetime.utcnow)
    spoonacular_id = Column(Integer, nullable=False)

    user = relationship("User", back_populates="meals")

## ------------------ POSTS TABLE ------------------
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    media_url = Column(String, nullable=True)
    likes = Column(Integer, default=0)
    date_posted = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

# ------------------ COMMENTS TABLE ------------------
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    date_posted = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")

# ------------------ ACHIEVEMENTS TABLE ------------------
class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)  # Badge name (e.g., "10 Workouts Completed")
    description = Column(String, nullable=False)  # Explanation of badge
    fa_icon_class = Column(String, nullable=False)  

# ------------------ GAMIFICATION BADGES TABLE ------------------
class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)  # Links to predefined achievements
    date_earned = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="badges")
    achievement = relationship("Achievement")  # Fetch details of the earned badge

    # ------------------ STREAKS TABLE  ------------------
class Streak(Base):
    __tablename__ = "streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # 'workout' or 'meal'
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="streaks")

    # ------------------ ACTIVITY LOG TABLE ------------------
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # 'workout' or 'meal'
    logged_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")

    # ------------------ LOGGED MEALS TABLE ------------------
class LoggedMeal(Base):
    __tablename__ = "logged_meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_item = Column(String, nullable=False)
    calories = Column(Integer, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fats = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logged_meals")


User.logged_meals = relationship("LoggedMeal", back_populates="user", cascade="all, delete-orphan")

# ------------------ WORKOUT LOGS TABLE ------------------
class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workout_name = Column(String, nullable=False)  # Name of the workout
    muscle_group = Column(String, nullable=False)  # Target muscle group (e.g., "Chest", "Back")
    equipment = Column(String, nullable=False)  # Equipment used (e.g., "Bodyweight", "Dumbbells")
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_logs")