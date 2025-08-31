from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os

# Security scheme for API key authentication
security = HTTPBearer()

class APIKeyAuth:
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API_KEY environment variable is required")
    
    def verify_api_key(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
        """Verify the API key from the Authorization header"""
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme. Use 'Bearer'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if credentials.credentials != self.api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return True

# Create a lazy global instance
_api_key_auth = None

def get_api_key_auth():
    """Get or create the API key auth instance lazily"""
    global _api_key_auth
    if _api_key_auth is None:
        _api_key_auth = APIKeyAuth()
    return _api_key_auth

def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Dependency to verify API key and return it"""
    api_key_auth = get_api_key_auth()
    api_key_auth.verify_api_key(credentials)
    return credentials.credentials

def require_api_key():
    """Decorator-style dependency for API key authentication"""
    return Depends(get_api_key) 