from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create a connection to PostgreSQL
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define a base class for models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        
#  Retrieve Spoonacular API Key
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

#  Debugging: Print the key to verify it's loaded
print("Spoonacular API Key:", SPOONACULAR_API_KEY)
