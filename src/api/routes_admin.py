from math import ceil
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from src.api.dependencies import require_admin
from src.db.session import get_db
from src.models.user import User, UserRole
from src.schemas.user import PaginatedUsers, UserRead

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


@router.get(
    "/users",
    response_model=PaginatedUsers,
)
def list_users(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    role: UserRole | None = Query(
        default=None,
    ),
    email: str | None = Query(
        default=None,
        min_length=1,
    ),
    sort_by: Literal[
        "id",
        "email",
        "created_at",
    ] = Query(
        default="id",
    ),
    sort_order: Literal[
        "asc",
        "desc",
    ] = Query(
        default="asc",
    ),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> PaginatedUsers:
    filters = []

    if role is not None:
        filters.append(
            User.role == role.value
        )

    if email is not None:
        filters.append(
            User.email.ilike(
                f"%{email}%"
            )
        )

    count_statement = select(
        func.count(User.id)
    ).where(*filters)

    total = db.scalar(
        count_statement
    ) or 0

    sort_columns = {
        "id": User.id,
        "email": User.email,
        "created_at": User.created_at,
    }

    sort_column = sort_columns[
        sort_by
    ]

    ordering = (
        asc(sort_column)
        if sort_order == "asc"
        else desc(sort_column)
    )

    offset = (
        page - 1
    ) * page_size

    statement = (
        select(User)
        .where(*filters)
        .order_by(ordering)
        .offset(offset)
        .limit(page_size)
    )

    users = db.scalars(
        statement
    ).all()

    pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    return PaginatedUsers(
        items=[
            UserRead.model_validate(
                user
            )
            for user in users
        ],
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )