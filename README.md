# Wellness Backend

This is the backend for **Wellness**, a full-stack final year project designed to support healthy habit building through personalized meal planning, workout tracking, and AI-based suggestions.

## Key Features

- JWT-based user authentication
- Meal logging and streak tracking
- Workout logging by type and muscle group
- Community posting and commenting
- Achievement tracking system
- AI-powered habit suggestions (implemented using custom logic)
- Connected to a React Native frontend

## 🛠️ Tech Stack

- Python with FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Pydantic models
- Alembic for database migrations

## 📁 Project Structure
fitness-backend/
├── app/ # Main backend logic and route handlers
├── main.py # FastAPI entry point
├── alembic/ # DB migration scripts
├── uploads/ # Uploaded media files (e.g., profile pictures)
├── tests/ # Test files


##  How to Run

```bash
# Create a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload


