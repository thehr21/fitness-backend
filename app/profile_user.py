from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from app.database import get_db
from app.models import User
from app.schemas import UserProfileUpdate

router = APIRouter()

#  Ensure upload directory exists
UPLOAD_DIR = "uploads/profile_pictures"
os.makedirs(UPLOAD_DIR, exist_ok=True)

#  Backend base URL (Change if necessary)
BASE_URL = "http://192.168.0.229:8000/uploads/profile_pictures"

@router.get("/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch user profile details.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "full_name": user.full_name,
        "username": user.username,
        "email": user.email,
        "profile_picture": user.profile_picture,
        "current_weight": user.current_weight,  # Ensure current_weight is included
    }

@router.put("/{user_id}")  #  Removed "profile" to avoid redundancy
def update_profile(user_id: int, profile_data: UserProfileUpdate, db: Session = Depends(get_db)):
    """
    Update user profile details (full_name, username, and current_weight).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user details
    user.full_name = profile_data.full_name
    user.username = profile_data.username
    user.current_weight = profile_data.current_weight  # Ensure the weight is updated as well
    db.commit()
    
    return {"message": "Profile updated successfully"}

@router.post("/{user_id}/upload-picture")  #  Removed "profile" to avoid redundancy
def upload_profile_picture(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Uploads a profile picture for the user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    #  Validate file type
    allowed_types = ["image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG and PNG files are allowed")

    #  Define correct file path
    file_extension = "jpg" if file.content_type == "image/jpeg" else "png"
    file_path = os.path.join(UPLOAD_DIR, f"{user_id}.{file_extension}")

    #  Save the file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    #  Store the accessible profile picture URL
    user.profile_picture = f"{BASE_URL}/{user_id}.{file_extension}"
    db.commit()

    return {"message": "Profile picture uploaded successfully", "profile_picture": user.profile_picture}
