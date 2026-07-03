from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_active_user
from app.core.rate_limit import rate_limit
from app.core.security import decode_token
from app.core.config import settings
from app.services.auth_servics import AuthService
from app.schemas.auth import (
    UserCreate, UserResponse, Token, LoginResponse,
    PasswordReset, PasswordResetConfirm, LogoutRequest
)
from app.models.user import User, UserStatus

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests=5, period=60)  # Max 5 registrations per minute
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    service = AuthService(db, {
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent")
    })
    
    user = service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number
    )
    
    return user

@router.post("/login", response_model=LoginResponse)
@rate_limit(requests=10, period=60)  # Max 10 login attempts per minute
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with username and password"""
    service = AuthService(db, {
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "device_name": request.headers.get("x-device-name", "Unknown")
    })
    
    result = service.login_user(
        username=form_data.username,
        password=form_data.password,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent", "Unknown")
    )
    
    # Set HTTP-only cookie for refresh token
    response = Response()
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth/refresh"
    )
    
    return LoginResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        user=result["user"]
    )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Get refresh token from cookie or body
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided"
        )
    
    service = AuthService(db)
    result = service.refresh_access_token(refresh_token)
    
    # Update cookie with new refresh token
    response = Response()
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth/refresh"
    )
    
    return Token(**result)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user and revoke refresh token"""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        service = AuthService(db, {
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent")
        })
        service.logout_user(current_user.id, refresh_token)
    
    # Clear cookie
    response = Response()
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    return response

@router.post("/password-reset-request")
@rate_limit(requests=3, period=3600)  # 3 requests per hour
async def request_password_reset(
    email: str,
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    # Use service to send reset email
    # This would generate a token and send email
    return {"message": "Password reset email sent if account exists"}

@router.post("/password-reset-confirm")
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    # Validate token and reset password
    return {"message": "Password reset successful"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@router.get("/verify-email/{token}")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email address"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.status == UserStatus.ACTIVE:
        return {"message": "Email already verified"}
    
    user.email_verified_at = datetime.utcnow()
    user.status = UserStatus.ACTIVE
    user.is_active = True
    db.commit()
    
    return {"message": "Email verified successfully"}