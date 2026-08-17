from contextvars import ContextVar
from uuid import uuid4

request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def generate_request_id() -> str:
    return str(uuid4())


def get_request_id() -> str | None:
    return request_id_context.get()


def set_request_id(
    request_id: str,
):
    return request_id_context.set(
        request_id
    )


def reset_request_id(token) -> None:
    request_id_context.reset(token)