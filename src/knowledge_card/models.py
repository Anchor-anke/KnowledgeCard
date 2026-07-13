"""Domain models for the CAPM learning MVP.

The models deliberately contain no persistence or HTTP concerns.  Services in
the individual modules own the business rules, while repositories only store
these immutable-ish records.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class Role(str, Enum):
    EDITOR = "CONTENT_EDITOR"
    REVIEWER = "REVIEWER"
    PUBLISHER = "PUBLISHER"


class ContentStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    UNPUBLISHED = "UNPUBLISHED"
    ARCHIVED = "ARCHIVED"


class Rating(str, Enum):
    FORGOT = "FORGOT"
    VAGUE = "VAGUE"
    REMEMBERED = "REMEMBERED"


class LearningStage(str, Enum):
    NEW = "NEW"
    LEARNING = "LEARNING"
    CONSOLIDATING = "CONSOLIDATING"
    STABLE = "STABLE"
    PAUSED = "PAUSED"


class FeedbackType(str, Enum):
    ERROR = "ERROR"
    CONFUSING = "CONFUSING"
    DUPLICATE = "DUPLICATE"


class FeedbackStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    WITHDRAWN = "WITHDRAWN"


@dataclass
class User:
    id: str
    wechat_open_id: str
    goal: Optional[str] = None
    onboarding_completed: bool = False
    subscription_authorized: bool = False
    new_card_limit: int = 10
    review_limit: int = 20
    reminder_time: str = "20:00"
    timezone: str = "Asia/Shanghai"
    roles: Tuple[Role, ...] = ()
    created_at: datetime = field(default=None)
    last_active_at: datetime = field(default=None)


@dataclass
class KnowledgePoint:
    id: str
    exam_id: str
    domain: str
    topic: str
    chapter: str
    objective: str
    difficulty: str
    created_by: str
    created_at: datetime


@dataclass
class CardVersion:
    id: str
    card_id: str
    knowledge_point_id: str
    version: int
    title: str
    conclusion: str
    explanation: str
    example: str
    recall_prompt: str
    reference_answer: str
    source: str
    source_locator: str
    created_by: str
    created_at: datetime
    status: ContentStatus = ContentStatus.DRAFT
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
    published_by: Optional[str] = None
    published_at: Optional[datetime] = None
    unpublished_reason: Optional[str] = None
    ai_generated: bool = False
    ai_model_version: Optional[str] = None


@dataclass(frozen=True)
class LearningRecord:
    id: str
    user_id: str
    card_id: str
    knowledge_point_id: str
    card_version_id: str
    session_id: str
    stage: LearningStage
    rating: Rating
    occurred_at: datetime
    client_version: str
    idempotency_key: str
    correction_of: Optional[str] = None


@dataclass
class ReviewPlan:
    user_id: str
    knowledge_point_id: str
    stage: LearningStage
    next_review_at: datetime
    last_reviewed_at: Optional[datetime]
    last_rating: Optional[Rating]
    consecutive_remembered: int
    interval_days: float
    algorithm_version: str
    overdue: bool = False
    revision: int = 0
    updated_at: Optional[datetime] = None


@dataclass(frozen=True)
class AuditEvent:
    id: str
    actor_id: str
    actor_role: Optional[Role]
    object_type: str
    object_id: str
    from_status: Optional[str]
    to_status: Optional[str]
    reason: Optional[str]
    request_id: str
    occurred_at: datetime


@dataclass
class ContentFeedback:
    id: str
    user_id: str
    card_id: str
    knowledge_point_id: str
    card_version_id: str
    feedback_type: FeedbackType
    description: Optional[str]
    status: FeedbackStatus
    severity: str
    created_at: datetime
    resolved_by: Optional[str] = None
    resolution: Optional[str] = None


@dataclass(frozen=True)
class NotificationTask:
    id: str
    user_id: str
    local_date: str
    due_count: int
    created_at: datetime
    status: str
    failure_reason: Optional[str] = None


@dataclass(frozen=True)
class DomainEvent:
    name: str
    occurred_at: datetime
    payload: Dict[str, Any]

