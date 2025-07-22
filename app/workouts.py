from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import requests
import os
from app.database import get_db
from app.models import User, WorkoutLog
from app.schemas import WorkoutLogRequest, WorkoutLogResponse


router = APIRouter()

# Load ExerciseDB API key from environment variables
EXERCISEDB_API_KEY = os.getenv("EXERCISEDB_API_KEY")
EXERCISEDB_BASE_URL = "https://exercisedb.p.rapidapi.com/exercises"

HEADERS = {
    "X-RapidAPI-Key": EXERCISEDB_API_KEY,
    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com"
}
#  New API Endpoint to Log Workouts
@router.post("/log-workout", response_model=WorkoutLogResponse)
def log_workout(request: WorkoutLogRequest, db: Session = Depends(get_db)):
    """
    Logs a workout in the database.
    """
    #  Validate user exists
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    #  Create and store the workout log
    new_log = WorkoutLog(
        user_id=request.user_id,
        workout_name=request.workout_name,
        muscle_group=request.muscle_group,
        equipment=request.equipment,
        timestamp=datetime.utcnow()
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log

@router.get("/logged-workouts/{user_id}", response_model=list[WorkoutLogResponse])
def get_logged_workouts(user_id: int, db: Session = Depends(get_db)):
    """
    Fetches all logged workouts for a specific user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logged_workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).all()

    if not logged_workouts:
        raise HTTPException(status_code=404, detail="No logged workouts found")

    return logged_workouts


@router.get("/workouts")
async def get_workouts(
    user_id: int = Query(None, description="User ID (Optional)"),
    workout_type: str = Query(..., description="Workout type: Home or Gym"),
    muscle_group: str = Query(..., description="Target muscle group (e.g., Chest, Back, Legs)"),
    db: Session = Depends(get_db)
):
    """
    Fetch workouts from ExerciseDB API based on user’s activity level, workout type, and muscle group.
    """

    print(f" DEBUG: Received request - user_id={user_id}, workout_type={workout_type}, muscle_group={muscle_group}")

    try:
        # Ensure user_id is provided
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        # Fetch user data
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        activity_level = user.activity_level.lower()  # Retrieve activity level
        print(f" DEBUG: Retrieved activity level from DB: {activity_level}")

        # Map activity level to intensity
        activity_map = {
            "sedentary": "beginner",
            "light": "beginner",
            "moderate": "intermediate",
            "active": "intermediate",
            "super": "advanced"
        }
        intensity = activity_map.get(activity_level, "beginner")

        print(f" DEBUG: Mapped activity level: {activity_level} -> {intensity}")

        # Fetch exercises for the selected muscle group
        valid_muscle_groups = ["back", "cardio", "chest", "lower arms", "lower legs",
                                "neck", "shoulders", "upper arms", "upper legs", "waist"]
        muscle_group = muscle_group.strip().lower()

        if muscle_group not in valid_muscle_groups:
            raise HTTPException(status_code=400, detail=f"Invalid muscle group: {muscle_group}")

        api_url = f"{EXERCISEDB_BASE_URL}/bodyPart/{muscle_group}?limit=100"
        response = requests.get(api_url, headers=HEADERS)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch workouts")

        exercises = response.json()
        print(f" DEBUG: API returned {len(exercises)} exercises")

        #  Fetch ALL Bodyweight Exercises for Home Workouts
        if workout_type.lower() == "home":
            bodyweight_url = f"{EXERCISEDB_BASE_URL}/equipment/body%20weight?limit=100"
            bodyweight_response = requests.get(bodyweight_url, headers=HEADERS)
            if bodyweight_response.status_code == 200:
                bodyweight_exercises = bodyweight_response.json()
                exercises.extend([
                    ex for ex in bodyweight_exercises
                    if muscle_group in ex["target"].lower()
                ])

        print(f" DEBUG: Final Combined Exercises Count: {len(exercises)}")

        #  Improved Filtering Logic
        filtered_workouts = []
        for ex in exercises:
            if workout_type.lower() == "home" and ex["equipment"].strip().lower() == "body weight":
                filtered_workouts.append(ex)
            elif workout_type.lower() == "gym" and ex["equipment"].strip().lower() != "body weight":
                filtered_workouts.append(ex)

        #  Return Workouts with Correct gifUrl and `instructions`
        final_workouts = [
            {
                "id": ex["id"],
                "name": ex["name"],
                "equipment": ex["equipment"],
                "gifUrl": ex["gifUrl"],  
                "video_url": f"https://www.youtube.com/results?search_query={ex['name'].replace(' ', '+')}+exercise",
                "target_muscle": ex["target"],
                "difficulty": intensity,
                "instructions": ex.get("instructions", [])
            }
            for ex in filtered_workouts
        ]

        if not final_workouts:
            raise HTTPException(status_code=404, detail="No workouts found for the given criteria.")

        print(f"📌 DEBUG: Returning {len(final_workouts)} workouts")
        return {"workouts": final_workouts}

    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))