# app/community.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from typing import List

router = APIRouter()

# ------------------- Community Routes ------------------- #

@router.get("/posts", response_model=List[schemas.PostResponse])
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()

    post_responses = []
    for post in posts:
        user = db.query(models.User).filter(models.User.id == post.user_id).first()
        if user:
            post_responses.append(
                schemas.PostResponse(
                    id=post.id,
                    content=post.content,
                    media_url=post.media_url,
                    likes=post.likes,
                    date_posted=post.date_posted,
                    user=schemas.UserPublic(
                        id=user.id,
                        full_name=user.full_name,
                        username=user.username,
                        profile_picture=user.profile_picture,
                    ),
                )
            )
    return post_responses


@router.post("/create-post", response_model=schemas.PostResponse)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    # moderation removed for testing

    new_post = models.Post(
        user_id=post.user_id,
        content=post.content,
        media_url=post.media_url or None,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    user = db.query(models.User).filter(models.User.id == post.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.PostResponse(
        id=new_post.id,
        content=new_post.content,
        media_url=new_post.media_url,
        likes=new_post.likes,
        date_posted=new_post.date_posted,
        user=schemas.UserPublic(
            id=user.id,
            full_name=user.full_name,
            username=user.username,
            profile_picture=user.profile_picture,
        ),
    )


@router.get("/comments/{post_id}", response_model=List[schemas.CommentResponse])
def get_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).all()

    comment_responses = []
    for comment in comments:
        user = db.query(models.User).filter(models.User.id == comment.user_id).first()
        if user:
            comment_responses.append(
                schemas.CommentResponse(
                    id=comment.id,
                    post_id=comment.post_id,
                    content=comment.content,
                    date_posted=comment.date_posted,
                    user=schemas.UserPublic(
                        id=user.id,
                        full_name=user.full_name,
                        username=user.username,
                        profile_picture=user.profile_picture,
                    ),
                )
            )
    return comment_responses


@router.post("/add-comment", response_model=schemas.CommentResponse)
def add_comment(comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    # moderation removed for testing

    new_comment = models.Comment(
        post_id=comment.post_id,
        user_id=comment.user_id,
        content=comment.content,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    user = db.query(models.User).filter(models.User.id == comment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return schemas.CommentResponse(
        id=new_comment.id,
        post_id=new_comment.post_id,
        content=new_comment.content,
        date_posted=new_comment.date_posted,
        user=schemas.UserPublic(
            id=user.id,
            full_name=user.full_name,
            username=user.username,
            profile_picture=user.profile_picture,
        ),
    )


@router.post("/like/{post_id}")
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.likes += 1 if not post.likes else -1
    db.commit()
    return {"message": "Like toggled successfully", "likes": post.likes}
