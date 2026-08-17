from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.dependencies import require_admin
from src.db.session import get_db
from src.models.user import User
from src.schemas.user import UserRead

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


@router.get(
    "/users",
    response_model=list[UserRead],
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[UserRead]:
    users = db.scalars(
        select(User).order_by(User.id)
    ).all()

    return [
        UserRead.model_validate(user)
        for user in users
    ]