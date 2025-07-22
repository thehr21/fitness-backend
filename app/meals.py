import os
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

router = APIRouter()

# Define cache duration (2 days)
CACHE_DURATION = timedelta(days=2)

@router.get("/{goal}", response_model=list[schemas.MealResponse])
def get_meals(
    goal: str,
    refresh: bool = False,
    filter: str = Query(None, description="Dietary filter like vegan, vegetarian, gluten-free, diabetic, low-carb, keto"),
    db: Session = Depends(get_db),
):
    print(f" API Called: Fetching meals for goal = '{goal}', refresh = {refresh}, filter = {filter}")

    if refresh:
        print(" Deleting old meals before fetching new ones...")
        deleted_rows = db.query(models.Meal).filter(models.Meal.goal == goal).delete(synchronize_session=False)
        db.commit()
        print(f" Deleted {deleted_rows} old meals!")


    offset = random.randint(0, 100)
    print(f" Random offset applied: {offset}")

    url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={SPOONACULAR_API_KEY}&number=10&addRecipeNutrition=true&offset={offset}"

    if filter:
        filter = filter.lower()
        if filter == "vegan":
            url += "&diet=vegan"
        elif filter == "vegetarian":
            url += "&diet=vegetarian"
        elif filter == "gluten-free":
            url += "&intolerances=gluten"
        elif filter == "diabetic":
            url += "&maxSugar=5"
        elif filter == "low-carb":
            url += "&maxCarbs=20"
        elif filter == "keto":
            url += "&diet=ketogenic"

    if goal.lower() == "lose weight":
        url += "&maxCalories=500&minProtein=20&maxCarbs=50&maxFat=20"
    elif goal.lower() == "muscle gain":
        url += "&minCalories=600&maxCalories=1000&minProtein=30&minCarbs=50&maxFat=40"
    elif goal.lower() == "maintenance":
        url += "&minCalories=500&maxCalories=800&minProtein=20&maxCarbs=50&maxFat=30"

    print(f" Final API Request URL: {url}")
    response = requests.get(url)

    if response.status_code == 402:
        raise HTTPException(status_code=402, detail="Your daily Spoonacular API limit has been reached. Try again tomorrow.")

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch meals from Spoonacular API")

    data = response.json()
    if "results" not in data:
        raise HTTPException(status_code=404, detail="No meals found")

    meals = []
    for item in data["results"]:
        spoonacular_id = item["id"]
        protein, carbs, fats, calories = 0, 0, 0, 0

        for nutrient in item.get("nutrition", {}).get("nutrients", []):
            if nutrient["name"].lower() == "protein":
                protein = nutrient["amount"]
            elif nutrient["name"].lower() == "carbohydrates":
                carbs = nutrient["amount"]
            elif nutrient["name"].lower() == "fat":
                fats = nutrient["amount"]
            elif nutrient["name"].lower() == "calories":
                calories = nutrient["amount"]

        if goal.lower() == "lose weight":
            if calories > 500 or protein < 20 or carbs > 50 or fats > 20:
                continue
        elif goal.lower() == "muscle gain":
            if calories < 600 or calories > 1000 or protein < 30 or carbs < 50 or fats > 40:
                continue
        elif goal.lower() == "maintenance":
            if calories < 500 or calories > 800 or protein < 20 or carbs < 50 or fats > 30:
                continue


        meal = models.Meal(
            food_item=item["title"],
            image=item.get("image", ""),
            calories=calories,
            protein=protein,
            carbs=carbs,
            fats=fats,
            goal=goal,
            date=datetime.utcnow(),
            spoonacular_id=spoonacular_id
        )
        db.add(meal)
        meals.append(meal)

    db.commit()
    print(f" Stored {len(meals)} new meals in the database")
    return meals