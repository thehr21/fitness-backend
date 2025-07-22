from sqlalchemy.sql import text  #  Import text()
from app.database import SessionLocal

db = SessionLocal()
try:
    db.execute(text("SELECT 1"))  #  Use text() for raw SQL queries
    print(" Database is connected!")
except Exception as e:
    print(" Database connection failed:", e)
finally:
    db.close()
