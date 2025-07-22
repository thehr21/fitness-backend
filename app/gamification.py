from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Streak, Achievement, Badge, User, ActivityLog
from pydantic import BaseModel
from sqlalchemy import extract, func

router = APIRouter()

class AchievementResponse(BaseModel):
    id: int
    name: str
    fa_icon_class: str

@router.get("/all-achievements", response_model=list[AchievementResponse])
def get_all_achievements(db: Session = Depends(get_db)):
    """
    Fetches all achievements (both unlocked & locked).
    Used to display locked badges in the UI.
    """
    achievements = db.query(Achievement).all()

    return [
        {
            "id": ach.id,
            "name": ach.name,
            #  Remove "fas " prefix before sending to frontend
            "fa_icon_class": ach.fa_icon_class.replace("fas ", "").strip() if ach.fa_icon_class and "fa-" in ach.fa_icon_class else "question-circle"
        }
        for ach in achievements
    ]


@router.get("/user-progress")
def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    """
    Fetches user's current streaks, best streaks, and total logs.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch all streaks for the user
    streaks = db.query(Streak).filter(Streak.user_id == user_id).all()

    # Fetch total logs for workout and meal
    total_logs = {
        "workout": db.query(ActivityLog).filter(ActivityLog.user_id == user_id, ActivityLog.type == "workout").count(),
        "meal": db.query(ActivityLog).filter(ActivityLog.user_id == user_id, ActivityLog.type == "meal").count(),
    }

    return {
        "current_streaks": {streak.type: streak.current_streak for streak in streaks},
        "best_streaks": {streak.type: streak.best_streak for streak in streaks},
        "total_logs": total_logs,
    }


@router.get("/badges")
def get_user_badges(user_id: int, db: Session = Depends(get_db)):
    """
    Fetches all badges earned by the user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    badges = db.query(Badge).filter(Badge.user_id == user_id).all()

    return [
        {
            "id": badge.achievement_id,  #  Return achievement_id to match frontend check
            "name": badge.achievement.name,
            "fa_icon_class": badge.achievement.fa_icon_class,
        }
        for badge in badges
    ]



class ActivityLogRequest(BaseModel):
    user_id: int
    activity_type: str  # "workout" or "meal"

@router.post("/log-activity")
def log_activity(data: ActivityLogRequest, db: Session = Depends(get_db)):
    """
    Logs an activity (workout or meal), updates the user's streak, and checks for new badges.
    """

    #  Step 1: Validate activity type
    if data.activity_type not in ["workout", "meal"]:
        raise HTTPException(status_code=400, detail="Invalid activity type. Use 'workout' or 'meal'.")

    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = datetime.utcnow().date()

    #  Step 2: Allow multiple logs but only update streak once per day
    existing_log = db.query(ActivityLog).filter(
        ActivityLog.user_id == data.user_id,
        ActivityLog.type == data.activity_type,
        func.date(ActivityLog.logged_at) == today
    ).first()

    streak_updated = False
    if not existing_log:
        streak_updated = True  #  Streak will update if this is the first log today

    #  Step 3: Log the activity
    new_log = ActivityLog(user_id=data.user_id, type=data.activity_type, logged_at=datetime.utcnow())
    db.add(new_log)
    db.commit()

    print(f"Activity logged: {data.activity_type} for user {data.user_id} at {new_log.logged_at}")

    #  Step 4: Ensure streak exists before calling `check_and_award_badge()`
    streak = db.query(Streak).filter(Streak.user_id == data.user_id, Streak.type == data.activity_type).first()
    
    if streak_updated:
        if streak:
            last_logged_day = streak.last_updated.date() if streak.last_updated else None
            print(f"🔍 Last logged day: {last_logged_day}, Today: {today}")

            if last_logged_day == today - timedelta(days=1):  # If logged yesterday, increase streak
                streak.current_streak += 1
                print(f" Streak increased! New streak: {streak.current_streak}")
            elif last_logged_day != today:  # If not logged today and not yesterday, reset streak
                print(" Missed a day. Resetting streak.")
                streak.current_streak = 1  # Reset streak

            streak.best_streak = max(streak.best_streak, streak.current_streak)
            streak.last_updated = datetime.utcnow()

        else:
            print("🔹 No streak found. Creating new streak entry.")
            streak = Streak(user_id=data.user_id, type=data.activity_type, current_streak=1, best_streak=1, last_updated=datetime.utcnow())
            db.add(streak)

        db.commit()
        print(f" Streaks updated: Current: {streak.current_streak}, Best: {streak.best_streak}")

    #  Step 5: Count total logs for this activity type
    total_logs = db.query(ActivityLog).filter(
        ActivityLog.user_id == data.user_id,
        ActivityLog.type == data.activity_type
    ).count()

    print(f" Total {data.activity_type} logs: {total_logs}")

    #  Step 6: Call badge function only if streak exists
    check_and_award_badge(data.user_id, data.activity_type, streak.current_streak if streak else None, total_logs, db)

    return {
        "message": "Activity logged successfully",
        "current_streak": streak.current_streak if streak_updated else None,
        "best_streak": streak.best_streak if streak_updated else None,
        "total_logs": total_logs  #  Ensure total logs are updated in response
    }

#  Function to check and award badges
def check_and_award_badge(user_id: int, activity_type: str, current_streak: int, total_logs: int, db: Session):
    """
    Checks if a user has reached an achievement milestone and awards a badge if applicable.
    """

    milestones = {
        "workout": {
            "streaks": {
                7: "7-Day Workout Streak",
                14: "14-Day Workout Streak",
                30: "30-Day Workout Streak",
                60: "60-Day Workout Streak"
            },
            "logs": {
                1: "First Workout Completed",
                10: "10 Workouts Completed",
                25: "25 Workouts Completed",
                50: "50 Workouts Completed",
                100: "100 Workouts Completed"
            }
        },
        "meal": {
            "streaks": {
                7: "7-Day Meal Logging Streak",
                14: "14-Day Meal Logging Streak",
                30: "30-Day Meal Logging Streak",
                60: "60-Day Meal Logging Streak"
            },
            "logs": {
                1: "First Meal Logged",
                10: "10 Meals Logged",
                25: "25 Meals Logged",
                50: "50 Meals Logged",
                100: "100 Meals Logged"
            }
        }
    }

    new_badges = []  # Store new badges to add

    #  Check for streak-based achievements
    for streak_days, badge_name in milestones[activity_type]["streaks"].items():
        if current_streak == streak_days:
            print(f" User {user_id} qualifies for streak-based badge: {badge_name}")
            award_badge(user_id, badge_name, db, new_badges)

    #  Check for log-based achievements
    for log_count, badge_name in milestones[activity_type]["logs"].items():
        if total_logs == log_count:
            print(f" User {user_id} qualifies for log-based badge: {badge_name}")
            award_badge(user_id, badge_name, db, new_badges)

    #  Check for special achievements
    if activity_type == "workout":
        total_meal_logs = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id,
            ActivityLog.type == "meal"
        ).count()

        if total_logs >= 30 and total_meal_logs >= 30:
            award_badge(user_id, "Consistency King", db, new_badges)
        if total_logs >= 50 and total_meal_logs >= 50:
            award_badge(user_id, "Halfway to Transformation", db, new_badges)
        if total_logs >= 100 and total_meal_logs >= 100:
            award_badge(user_id, "Fitness Legend", db, new_badges)

        early_riser_logs = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id,
            ActivityLog.type == "workout",
            extract('hour', ActivityLog.logged_at) < 6
        ).count()

        night_owl_logs = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id,
            ActivityLog.type == "workout",
            extract('hour', ActivityLog.logged_at) >= 22
        ).count()

        if early_riser_logs >= 10:
            award_badge(user_id, "Early Riser", db, new_badges)
        if night_owl_logs >= 10:
            award_badge(user_id, "Night Owl", db, new_badges)

    #  Commit all new badges at once
    if new_badges:
        db.add_all(new_badges)
        db.commit()
        print(f"🏅 Awarded {len(new_badges)} new badges to user {user_id}")

#  Function to award a badge
def award_badge(user_id: int, badge_name: str, db: Session, new_badges: list):
    """
    Awards a badge to a user if they don't already have it.
    """

    #  Find the achievement related to this badge
    achievement = db.query(Achievement).filter(Achievement.name == badge_name).first()
    if not achievement:
        print(f"⚠️ Achievement '{badge_name}' does not exist. Skipping.")
        return  # Skip if the achievement is missing

    # Check if the user already has this badge
    existing_badge = db.query(Badge).filter(
        Badge.user_id == user_id,
        Badge.achievement_id == achievement.id
    ).first()

    if not existing_badge:
        #  Add new badge to the list for batch insertion
        new_badges.append(Badge(user_id=user_id, achievement_id=achievement.id, date_earned=datetime.utcnow()))
        print(f"🏅 Awarded badge: {badge_name} to user {user_id}")