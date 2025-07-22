# path: app/ai_suggestions.py
import sys
import datetime
import torch
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

sys.path.append(r"C:\Users\hassa\WellnessProject")
from postprocess_output import postprocess_output
from app.database import get_db
from app.models import User, LoggedMeal, Streak

router = APIRouter(prefix="/ai", tags=["AI Suggestions"])

from transformers import T5Tokenizer, T5ForConditionalGeneration
model_path = r"C:\Users\hassa\WellnessProject\MODEL"
print("Loading model from:", model_path)

tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(" Model loaded on:", device)

# ----------------- Helpers ------------------ #

def build_model_input(user, avg_calories, avg_protein, meal_streak, workout_streak):
    return (
        f"goal: {user.goal}; activity_level: {user.activity_level}; "
        f"current_weight: {user.current_weight}; target_weight: {user.target_weight}; "
        f"avg_calories: {avg_calories:.2f}; avg_protein: {avg_protein:.2f}; "
        f"meal_streak: {meal_streak}; workout_streak: {workout_streak}; "
        f"feedback_category: motivation; user_segment: balanced; tone: coach"
    )

# ------------------ Route ------------------ #

@router.get("/suggestions/{user_id}")
def get_user_suggestions(user_id: int, db: Session = Depends(get_db)):
    print(f" API called: /ai/suggestions/{user_id}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = datetime.datetime.utcnow().date()
    seven_days_ago = today - datetime.timedelta(days=6)

    # Pull meals from last 7 days
    meals = db.query(
        func.date(LoggedMeal.timestamp).label("day"),
        func.sum(LoggedMeal.calories).label("daily_calories"),
        func.sum(LoggedMeal.protein).label("daily_protein")
    ).filter(
        LoggedMeal.user_id == user_id,
        func.date(LoggedMeal.timestamp) >= seven_days_ago
    ).group_by(func.date(LoggedMeal.timestamp)).all()

    if meals:
        total_calories = sum(m.daily_calories or 0 for m in meals)
        total_protein = sum(m.daily_protein or 0 for m in meals)
        avg_calories = total_calories / 7
        avg_protein = total_protein / 7
    else:
        avg_calories = 0.0
        avg_protein = 0.0

    meal_streak_obj = db.query(Streak).filter_by(user_id=user_id, type="meal").first()
    workout_streak_obj = db.query(Streak).filter_by(user_id=user_id, type="workout").first()

    meal_streak = meal_streak_obj.current_streak if meal_streak_obj else 0
    workout_streak = workout_streak_obj.current_streak if workout_streak_obj else 0

    print(f"📊 Meal Streak: {meal_streak}, Workout Streak: {workout_streak}")

    user_input = build_model_input(user, avg_calories, avg_protein, meal_streak, workout_streak)
    print("🧠 Model input:\n", user_input)

    inputs = tokenizer(user_input, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)

    model.eval()
    with torch.no_grad():
        output = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=128,
            num_beams=5,
            early_stopping=True
        )

    suggestion = tokenizer.decode(output[0], skip_special_tokens=True)
    print("Raw model output:\n", suggestion)

    #  Postprocess
    suggestion = postprocess_output(user_input, suggestion)
    print("Final suggestion:\n", suggestion)

    return {
        "suggestion": suggestion,
        "model_input": user_input
    }
