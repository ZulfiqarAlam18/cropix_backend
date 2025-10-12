# community/models.py
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cognito_user_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = relationship("Post", primaryjoin="User.cognito_user_id==Post.user_id", foreign_keys="Post.user_id", viewonly=True)
    comments = relationship("Comment", primaryjoin="User.cognito_user_id==Comment.user_id", foreign_keys="Comment.user_id", viewonly=True)
    likes = relationship("Like", primaryjoin="User.cognito_user_id==Like.user_id", foreign_keys="Like.user_id", viewonly=True)

class Post(Base):
    __tablename__ = "posts"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)  # Keep as string for backward compatibility
    username = Column(String, nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted = Column(Boolean, default=False)

    # For future: user_uuid = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", primaryjoin="Post.user_id==User.cognito_user_id", foreign_keys=[user_id], viewonly=True)
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    user_id = Column(String, nullable=False)  # Keep as string for backward compatibility
    username = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", primaryjoin="Comment.user_id==User.cognito_user_id", foreign_keys=[user_id], viewonly=True)

class Like(Base):
    __tablename__ = "likes"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    user_id = Column(String, nullable=False)  # Keep as string for backward compatibility
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="likes")
    user = relationship("User", primaryjoin="Like.user_id==User.cognito_user_id", foreign_keys=[user_id], viewonly=True)
