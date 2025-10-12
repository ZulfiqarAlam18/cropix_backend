# community/crud.py
from sqlalchemy.orm import Session
from . import models
from uuid import UUID

def create_post(db: Session, user_id: str, username: str, description: str, title: str = None, image_url: str = None):
    post = models.Post(user_id=user_id, username=username, title=title, description=description, image_url=image_url)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

def get_posts(db: Session, skip: int = 0, limit: int = 20):
    return db.query(models.Post).filter(models.Post.deleted == False).order_by(models.Post.created_at.desc()).offset(skip).limit(limit).all()

def get_post(db: Session, post_id: str):
    return db.query(models.Post).filter(models.Post.id == post_id, models.Post.deleted == False).first()

def delete_post(db: Session, post_id: str):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post:
        post.deleted = True
        db.commit()
    return post

def add_comment(db: Session, post_id: str, user_id: str, username: str, text: str):
    comment = models.Comment(post_id=post_id, user_id=user_id, username=username, text=text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def get_comments(db: Session, post_id: str, skip: int = 0, limit: int = 50):
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).order_by(models.Comment.created_at.asc()).offset(skip).limit(limit).all()

def toggle_like(db: Session, post_id: str, user_id: str):
    existing = db.query(models.Like).filter(models.Like.post_id == post_id, models.Like.user_id == user_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return False
    new_like = models.Like(post_id=post_id, user_id=user_id)
    db.add(new_like)
    db.commit()
    return True

def count_likes(db: Session, post_id: str):
    return db.query(models.Like).filter(models.Like.post_id == post_id).count()

def count_comments(db: Session, post_id: str):
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).count()
