"""Shared domain primitives and failure types."""

from datetime import datetime, timezone
from typing import Callable, Iterable, Optional, TypeVar
from uuid import uuid4


class DomainError(Exception):
    """Base class for expected business failures."""

    code = "DOMAIN_ERROR"


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"


class NotFoundError(DomainError):
    code = "NOT_FOUND"


class AuthorizationError(DomainError):
    code = "FORBIDDEN"


class ConflictError(DomainError):
    code = "CONFLICT"


def new_id(prefix: str) -> str:
    return "{}_{}".format(prefix, uuid4().hex)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


Clock = Callable[[], datetime]


T = TypeVar("T")


def require(condition: bool, message: str, error_type=ValidationError) -> None:
    if not condition:
        raise error_type(message)


def first_or_none(items: Iterable[T]) -> Optional[T]:
    return next(iter(items), None)

