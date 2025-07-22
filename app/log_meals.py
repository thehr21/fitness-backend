from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime  #  Import datetime for timestamps
from app.database import get_db
from app import models, schemas
import traceback

router = APIRouter(prefix="/log-meals", tags=["log-meals"], include_in_schema=True)

@router.post("/", response_model=schemas.LoggedMealResponse)
def log_meal(request: schemas.LoggedMealRequest, db: Session = Depends(get_db)):
    """
    Logs a meal for a user.
    """
    try:
        print(f" Received Log Meal Request: {request.dict()}")

        new_log = models.LoggedMeal(
            user_id=request.user_id,
            food_item=request.food_item,
            calories=request.calories,
            protein=request.protein,
            carbs=request.carbs,
            fats=request.fats,
            timestamp=datetime.utcnow()  # Ensure timestamp is saved
        )

        db.add(new_log)
        db.commit()
        db.refresh(new_log)

        print(f" Meal logged successfully: {new_log}")
        return new_log

    except Exception as e:
        db.rollback()
        print(f" Error logging meal: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to log meal: {str(e)}")


@router.get("/{user_id}", response_model=list[schemas.LoggedMealResponse])
def get_logged_meals(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch all logged meals for a specific user.
    """
    print(f" Fetching logged meals for user {user_id}")

    logged_meals = db.query(models.LoggedMeal).filter(models.LoggedMeal.user_id == user_id).all()

    if not logged_meals:
        print(f" No logged meals found for user {user_id}")
        raise HTTPException(status_code=404, detail="No logged meals found")

    print(f" Found {len(logged_meals)} logged meals for user {user_id}")
    return logged_meals 