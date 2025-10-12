# community/user_routes.py - User management with Cognito integration
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from db import get_db
from . import schemas, models
from auth import require_auth, optional_auth
import uuid
from datetime import datetime

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/me", response_model=schemas.UserProfile)
def get_current_user_profile(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current authenticated user's profile"""
    user = db.query(models.User).filter(
        models.User.cognito_user_id == current_user["user_id"]
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please create your profile first."
        )
    
    return schemas.UserProfile(
        id=str(user.id),
        cognito_user_id=user.cognito_user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/profile", response_model=schemas.UserProfile)
def create_or_update_user_profile(
    profile_data: schemas.UserProfileCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create or update user profile from Cognito user info"""
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        models.User.cognito_user_id == current_user["user_id"]
    ).first()
    
    if existing_user:
        # Update existing user
        existing_user.username = profile_data.username
        existing_user.email = profile_data.email
        existing_user.display_name = profile_data.display_name
        existing_user.bio = profile_data.bio
        existing_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_user)
        user = existing_user
    else:
        # Create new user
        user = models.User(
            cognito_user_id=current_user["user_id"],
            username=profile_data.username,
            email=profile_data.email,
            display_name=profile_data.display_name,
            bio=profile_data.bio
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return schemas.UserProfile(
        id=str(user.id),
        cognito_user_id=user.cognito_user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.put("/profile", response_model=schemas.UserProfile)
def update_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    user = db.query(models.User).filter(
        models.User.cognito_user_id == current_user["user_id"]
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please create your profile first."
        )
    
    # Update only provided fields
    if profile_update.display_name is not None:
        user.display_name = profile_update.display_name
    if profile_update.bio is not None:
        user.bio = profile_update.bio
    if profile_update.username is not None:
        # Check if username is already taken
        existing = db.query(models.User).filter(
            models.User.username == profile_update.username,
            models.User.id != user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken"
            )
        user.username = profile_update.username
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    return schemas.UserProfile(
        id=str(user.id),
        cognito_user_id=user.cognito_user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.get("/{user_id}", response_model=schemas.UserProfile)
def get_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(optional_auth)
):
    """Get user profile by ID (public endpoint)"""
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = db.query(models.User).filter(models.User.id == user_uuid).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return schemas.UserProfile(
        id=str(user.id),
        cognito_user_id=user.cognito_user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

@router.post("/sync", response_model=schemas.UserProfile)
def sync_user_from_cognito(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Sync/create user profile from Cognito token automatically"""
    # Extract info from Cognito token
    cognito_user_id = current_user["user_id"]
    username = current_user["username"]
    email = current_user["email"]
    
    # Check if user exists
    existing_user = db.query(models.User).filter(
        models.User.cognito_user_id == cognito_user_id
    ).first()
    
    if existing_user:
        # Update user info from token
        existing_user.email = email
        if existing_user.username != username:
            existing_user.username = username
        existing_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_user)
        user = existing_user
    else:
        # Create new user from Cognito token
        user = models.User(
            cognito_user_id=cognito_user_id,
            username=username,
            email=email,
            display_name=username  # Default display name to username
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return schemas.UserProfile(
        id=str(user.id),
        cognito_user_id=user.cognito_user_id,
        username=user.username,
        email=user.email,
        display_name=user.display_name,
        bio=user.bio,
        profile_image_url=user.profile_image_url,
        created_at=user.created_at,
        updated_at=user.updated_at
    )