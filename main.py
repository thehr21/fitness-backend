# app/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 
from app.auth import router as auth_router
from app.database import Base, engine
from app.meals import router as meals_router
from app.log_meals import router as log_meals_router
from app.workouts import router as workouts_router
from app.gamification import router as gamification_router
from app.community import router as community_router 
from app.profile_user import router as profile_router 
from app.ai_suggestions import router as ai_router 
import joblib # type: ignore
import numpy as np
import sys
sys.stdout.reconfigure(line_buffering=True)

print(" API LOADED")

# Load environment variables
load_dotenv()

#  Initialize Database
Base.metadata.create_all(bind=engine)

#  Initialize FastAPI
app = FastAPI()

#  Allow CORS (fixes "Failed to fetch" issue)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.0.229:3000", "exp://192.168.0.229:8081"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


#  Include routers with prefixes
app.include_router(auth_router, prefix="/auth")
app.include_router(meals_router, prefix="/meals")
app.include_router(log_meals_router)
app.include_router(workouts_router)
app.include_router(gamification_router, prefix="/gamification")
app.include_router(community_router, prefix="/community") 
app.include_router(profile_router, prefix="/profile") 
app.include_router(ai_router, prefix="/ai")
