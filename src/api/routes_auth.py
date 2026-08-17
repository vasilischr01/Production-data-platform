from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
    db: Session = Depends(get_db),
) -> UserRead:
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
    db: Session = Depends(get_db),
) -> TokenResponse:
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
