"""In-memory infrastructure adapters used by the MVP and its tests.

The services depend on these small repositories rather than on dictionaries.
Replacing them with SQL or another store does not change the domain modules.
"""

from typing import Dict, Iterable, List, Optional, Tuple

from .models import (
    AuditEvent,
    CardVersion,
    ContentFeedback,
    DomainEvent,
    LearningRecord,
    NotificationTask,
    ReviewPlan,
    User,
    KnowledgePoint,
)


class UserRepository:
    def __init__(self):
        self.by_id: Dict[str, User] = {}
        self.by_wechat_id: Dict[str, str] = {}

    def save(self, user: User) -> User:
        self.by_id[user.id] = user
        self.by_wechat_id[user.wechat_open_id] = user.id
        return user

    def get(self, user_id: str) -> Optional[User]:
        return self.by_id.get(user_id)

    def find_by_wechat_id(self, value: str) -> Optional[User]:
        user_id = self.by_wechat_id.get(value)
        return self.get(user_id) if user_id else None


class KnowledgePointRepository:
    def __init__(self):
        self.items: Dict[str, KnowledgePoint] = {}

    def save(self, item: KnowledgePoint) -> KnowledgePoint:
        self.items[item.id] = item
        return item

    def get(self, item_id: str) -> Optional[KnowledgePoint]:
        return self.items.get(item_id)


class CardRepository:
    def __init__(self):
        self.items: Dict[str, CardVersion] = {}

    def save(self, item: CardVersion) -> CardVersion:
        self.items[item.id] = item
        return item

    def get(self, item_id: str) -> Optional[CardVersion]:
        return self.items.get(item_id)

    def versions_for_point(self, knowledge_point_id: str) -> List[CardVersion]:
        return sorted(
            (
                item
                for item in self.items.values()
                if item.knowledge_point_id == knowledge_point_id
            ),
            key=lambda item: (item.card_id, item.version),
        )

    def published(self) -> List[CardVersion]:
        return sorted(
            (item for item in self.items.values() if item.status.value == "PUBLISHED"),
            key=lambda item: (item.knowledge_point_id, item.card_id, item.version),
        )


class LearningRecordRepository:
    def __init__(self):
        self.items: Dict[str, LearningRecord] = {}
        self.by_idempotency: Dict[Tuple[str, str], str] = {}

    def save(self, item: LearningRecord) -> LearningRecord:
        self.items[item.id] = item
        self.by_idempotency[(item.user_id, item.idempotency_key)] = item.id
        return item

    def get(self, item_id: str) -> Optional[LearningRecord]:
        return self.items.get(item_id)

    def find_by_idempotency(
        self, user_id: str, idempotency_key: str
    ) -> Optional[LearningRecord]:
        item_id = self.by_idempotency.get((user_id, idempotency_key))
        return self.get(item_id) if item_id else None

    def for_user(self, user_id: str) -> List[LearningRecord]:
        return sorted(
            (item for item in self.items.values() if item.user_id == user_id),
            key=lambda item: item.occurred_at,
        )

    def latest_for_point(
        self, user_id: str, knowledge_point_id: str
    ) -> Optional[LearningRecord]:
        records = [
            item
            for item in self.for_user(user_id)
            if item.knowledge_point_id == knowledge_point_id
        ]
        return records[-1] if records else None


class ReviewPlanRepository:
    def __init__(self):
        self.items: Dict[Tuple[str, str], ReviewPlan] = {}

    def get(self, user_id: str, knowledge_point_id: str) -> Optional[ReviewPlan]:
        return self.items.get((user_id, knowledge_point_id))

    def save(self, item: ReviewPlan) -> ReviewPlan:
        self.items[(item.user_id, item.knowledge_point_id)] = item
        return item

    def for_user(self, user_id: str) -> List[ReviewPlan]:
        return sorted(
            (item for item in self.items.values() if item.user_id == user_id),
            key=lambda item: item.next_review_at,
        )


class AuditRepository:
    def __init__(self):
        self.items: List[AuditEvent] = []

    def save(self, item: AuditEvent) -> AuditEvent:
        self.items.append(item)
        return item

    def for_object(self, object_id: str) -> List[AuditEvent]:
        return [item for item in self.items if item.object_id == object_id]


class FeedbackRepository:
    def __init__(self):
        self.items: Dict[str, ContentFeedback] = {}

    def save(self, item: ContentFeedback) -> ContentFeedback:
        self.items[item.id] = item
        return item

    def get(self, item_id: str) -> Optional[ContentFeedback]:
        return self.items.get(item_id)

    def all(self) -> List[ContentFeedback]:
        return sorted(self.items.values(), key=lambda item: item.created_at)


class NotificationRepository:
    def __init__(self):
        self.items: Dict[Tuple[str, str], NotificationTask] = {}

    def get(self, user_id: str, local_date: str) -> Optional[NotificationTask]:
        return self.items.get((user_id, local_date))

    def save(self, item: NotificationTask) -> NotificationTask:
        self.items[(item.user_id, item.local_date)] = item
        return item


class EventRepository:
    def __init__(self):
        self.items: List[DomainEvent] = []

    def save(self, item: DomainEvent) -> DomainEvent:
        self.items.append(item)
        return item

