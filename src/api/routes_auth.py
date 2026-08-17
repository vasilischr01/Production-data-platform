from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.rate_limit import enforce_rate_limit
from src.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from src.db.session import get_db
from src.repositories.users import (
    create_user,
    get_user_by_email,
)
from src.schemas.user import (
    TokenResponse,
    UserCreate,
    UserRead,
)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> UserRead:
    enforce_rate_limit(
        request,
        limit=settings.auth_rate_limit_requests,
        window_seconds=settings.auth_rate_limit_window_seconds,
        scope="register",
    )
    existing_user = get_user_by_email(
        db,
        payload.email,
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user = create_user(
        db,
        email=payload.email,
        hashed_password=hash_password(
            payload.password
        ),
    )

    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    enforce_rate_limit(
        request,
        limit=settings.auth_rate_limit_requests,
        window_seconds=settings.auth_rate_limit_window_seconds,
        scope="login",
    )
    user = get_user_by_email(
        db,
        payload.email,
    )

    if (
        user is None
        or not verify_password(
            payload.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    token = create_access_token(
        subject=str(user.id),
        extra_claims={
            "role": user.role,
        },
    )

    return TokenResponse(
        access_token=token,
    )
