# community/schemas.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class PostCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID cannot be empty")
    username: str = Field(..., min_length=1, max_length=50, description="Username cannot be empty")
    title: Optional[str] = Field(None, max_length=200, description="Title cannot exceed 200 characters")
    description: str = Field(..., min_length=1, max_length=2000, description="Description cannot be empty or exceed 2000 characters")

class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    username: str
    title: Optional[str]
    description: str
    image_url: Optional[str]
    created_at: datetime
    likes_count: int = 0
    comments_count: int = 0

class CommentCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID cannot be empty")
    username: str = Field(..., min_length=1, max_length=50, description="Username cannot be empty")
    text: str = Field(..., min_length=1, max_length=1000, description="Comment text cannot be empty or exceed 1000 characters")

class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    post_id: str
    user_id: str
    username: str
    text: str
    created_at: datetime

class LikeResponse(BaseModel):
    liked: bool
    likes_count: int

# Authentication Schemas for AWS Cognito Integration
class UserProfile(BaseModel):
    """User profile information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    cognito_user_id: str
    username: str
    email: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserProfileCreate(BaseModel):
    """Schema for creating/updating user profile from Cognito"""
    username: str = Field(..., min_length=1, max_length=50)
    email: str = Field(..., description="Valid email address")
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)

class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = Field(None, min_length=1, max_length=50)

class CognitoUserInfo(BaseModel):
    """Information extracted from Cognito JWT token"""
    user_id: str = Field(..., description="Cognito user sub (unique ID)")
    username: str = Field(..., description="Username from Cognito")
    email: str = Field(..., description="Email from Cognito")
    email_verified: bool = False
