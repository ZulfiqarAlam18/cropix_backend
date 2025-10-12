# community/routes.py
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from db import get_db
from . import crud, schemas
import boto3, os, uuid

router = APIRouter(prefix="/community", tags=["community"])

def validate_uuid(uuid_string: str, field_name: str = "ID") -> None:
    """Validate UUID format and raise HTTPException if invalid"""
    try:
        UUID(uuid_string)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name} format")

def validate_non_empty(value: str, field_name: str) -> str:
    """Validate that a string is not empty after stripping whitespace"""
    if not value.strip():
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")
    return value.strip()

AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize S3 client only if AWS credentials are provided
s3 = None
if os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

def upload_file_to_s3(file: UploadFile, bucket: str, key: str) -> str:
    if not s3 or not bucket:
        raise HTTPException(status_code=503, detail="AWS S3 not configured")
    
    s3.upload_fileobj(
        file.file,
        bucket,
        key,
        ExtraArgs={"ACL": "public-read", "ContentType": file.content_type},
    )
    return f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"

@router.post("/posts", response_model=schemas.PostOut)
async def create_post(
    user_id: str = Form(..., min_length=1, max_length=100),
    username: str = Form(..., min_length=1, max_length=50),
    description: str = Form(..., min_length=1, max_length=2000),
    title: str = Form(None, max_length=200),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Validation
    user_id = validate_non_empty(user_id, "User ID")
    username = validate_non_empty(username, "Username")
    description = validate_non_empty(description, "Description")
    title = title.strip() if title else None
    
    image_url = None
    if image:
        if not s3 or not AWS_BUCKET_NAME:
            raise HTTPException(status_code=503, detail="Image upload not configured. AWS S3 credentials required.")
        
        ext = os.path.splitext(image.filename)[1]
        fname = f"{uuid.uuid4().hex}{ext}"
        key = f"community/{fname}"
        try:
            image_url = upload_file_to_s3(image, AWS_BUCKET_NAME, key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

    post = crud.create_post(db, user_id=user_id, username=username, description=description, title=title, image_url=image_url)
    
    # Convert UUID to string for Pydantic v2 validation
    post_data = {
        "id": str(post.id),
        "user_id": post.user_id,
        "username": post.username,
        "title": post.title,
        "description": post.description,
        "image_url": post.image_url,
        "created_at": post.created_at,
        "likes_count": crud.count_likes(db, str(post.id)),
        "comments_count": crud.count_comments(db, str(post.id))
    }
    return schemas.PostOut(**post_data)

@router.get("/posts", response_model=List[schemas.PostOut])
def get_posts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    result = []
    for p in posts:
        # Convert UUID to string for Pydantic v2 validation
        post_data = {
            "id": str(p.id),
            "user_id": p.user_id,
            "username": p.username,
            "title": p.title,
            "description": p.description,
            "image_url": p.image_url,
            "created_at": p.created_at,
            "likes_count": crud.count_likes(db, str(p.id)),
            "comments_count": crud.count_comments(db, str(p.id))
        }
        po = schemas.PostOut(**post_data)
        result.append(po)
    return result

@router.get("/posts/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: str, db: Session = Depends(get_db)):
    validate_uuid(post_id, "post ID")
    
    p = crud.get_post(db, post_id)
    if not p:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Convert UUID to string for Pydantic v2 validation
    post_data = {
        "id": str(p.id),
        "user_id": p.user_id,
        "username": p.username,
        "title": p.title,
        "description": p.description,
        "image_url": p.image_url,
        "created_at": p.created_at,
        "likes_count": crud.count_likes(db, post_id),
        "comments_count": crud.count_comments(db, post_id)
    }
    return schemas.PostOut(**post_data)

@router.post("/posts/{post_id}/comments", response_model=schemas.CommentOut)
def create_comment(post_id: str, comment: schemas.CommentCreate, db: Session = Depends(get_db)):
    validate_uuid(post_id, "post ID")
    
    # Validate comment data
    user_id = validate_non_empty(comment.user_id, "User ID")
    username = validate_non_empty(comment.username, "Username")
    text = validate_non_empty(comment.text, "Comment text")
    
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment_obj = crud.add_comment(db, post_id=post_id, user_id=user_id, username=username, text=text)
    
    # Convert UUID to string for Pydantic v2 validation
    comment_data = {
        "id": str(comment_obj.id),
        "post_id": str(comment_obj.post_id),
        "user_id": comment_obj.user_id,
        "username": comment_obj.username,
        "text": comment_obj.text,
        "created_at": comment_obj.created_at
    }
    return schemas.CommentOut(**comment_data)

@router.get("/posts/{post_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(post_id: str, db: Session = Depends(get_db)):
    validate_uuid(post_id, "post ID")
    
    comments = crud.get_comments(db, post_id)
    result = []
    for c in comments:
        comment_data = {
            "id": str(c.id),
            "post_id": str(c.post_id),
            "user_id": c.user_id,
            "username": c.username,
            "text": c.text,
            "created_at": c.created_at
        }
        result.append(schemas.CommentOut(**comment_data))
    return result

@router.post("/posts/{post_id}/like")
def like_post(post_id: str, user_id: str = Form(..., min_length=1, max_length=100), db: Session = Depends(get_db)):
    validate_uuid(post_id, "post ID")
    user_id = validate_non_empty(user_id, "User ID")
    
    success = crud.toggle_like(db, post_id, user_id)
    return {"liked": success, "likes_count": crud.count_likes(db, post_id)}

@router.delete("/posts/{post_id}")
def remove_post(post_id: str, user_id: str = Form(..., min_length=1, max_length=100), db: Session = Depends(get_db)):
    validate_uuid(post_id, "post ID")
    user_id = validate_non_empty(user_id, "User ID")
    
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Not found")
    if post.user_id != user_id:
        raise HTTPException(status_code=403, detail="Only owner can delete")
    crud.delete_post(db, post_id)
    return {"deleted": True}
