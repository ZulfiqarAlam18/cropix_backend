# auth.py - AWS Cognito authentication utilities
import jwt
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from functools import lru_cache
import json
from dotenv import load_dotenv

load_dotenv()

# AWS Cognito configuration
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

if not COGNITO_USER_POOL_ID:
    print("⚠️  Warning: COGNITO_USER_POOL_ID not set. Authentication will be optional for development.")

# JWT configuration
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}" if COGNITO_USER_POOL_ID else None
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json" if COGNITO_ISSUER else None

security = HTTPBearer(auto_error=False)

@lru_cache()
def get_cognito_public_keys():
    """Fetch and cache Cognito public keys for JWT verification"""
    if not COGNITO_JWKS_URL:
        return []
    
    try:
        response = requests.get(COGNITO_JWKS_URL, timeout=10)
        response.raise_for_status()
        return response.json()["keys"]
    except Exception as e:
        print(f"❌ Error fetching Cognito public keys: {e}")
        return []

def verify_cognito_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify AWS Cognito JWT token and return decoded payload"""
    if not COGNITO_USER_POOL_ID:
        print("⚠️  Warning: Cognito not configured, skipping token verification")
        return None
    
    try:
        # Get the token header
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing key ID"
            )
        
        # Find the correct public key
        public_keys = get_cognito_public_keys()
        public_key = None
        
        for key in public_keys:
            if key["kid"] == kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: public key not found"
            )
        
        # Verify and decode the token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=COGNITO_ISSUER,
            options={"verify_exp": True}
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Extract current user from JWT token (optional authentication)"""
    if not credentials:
        # Return None if no token provided (for optional auth)
        return None
    
    token = credentials.credentials
    payload = verify_cognito_token(token)
    
    if not payload:
        return None
    
    # Extract user info from Cognito token
    user_info = {
        "user_id": payload.get("sub"),  # Cognito user ID
        "username": payload.get("cognito:username") or payload.get("username"),
        "email": payload.get("email"),
        "email_verified": payload.get("email_verified", False)
    }
    
    return user_info

def require_auth(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require authentication - raise 401 if not authenticated"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid JWT token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def optional_auth(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Optional[Dict[str, Any]]:
    """Optional authentication - returns None if not authenticated"""
    return current_user