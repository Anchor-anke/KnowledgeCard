"""Application facade representing the API gateway boundary.

Clients should call this facade (or an HTTP adapter built on top of it), not
repositories.  Authentication, role checks and module orchestration remain on
the server side.
"""

from typing import Optional

from .analytics import AnalyticsService
from .catalog import CatalogService
from .content import ContentService
from .core import Clock, NotFoundError, require
from .feedback import FeedbackService
from .identity import IdentityService
from .learning import CardDeliveryService, LearningService
from .models import Role, User
from .notification import InMemoryWechatAdapter, NotificationService
from .repositories import (
    AuditRepository,
    CardRepository,
    EventRepository,
    FeedbackRepository,
    KnowledgePointRepository,
    LearningRecordRepository,
    NotificationRepository,
    ReviewPlanRepository,
    UserRepository,
)
from .review import ReviewService


class KnowledgeCardApplication:
    """A fully wired in-memory CAPM MVP."""

    def __init__(self, clock: Optional[Clock] = None):
        from .core import utc_now

        self.clock = clock or utc_now
        self.users = UserRepository()
        self.points = KnowledgePointRepository()
        self.cards = CardRepository()
        self.records = LearningRecordRepository()
        self.plans = ReviewPlanRepository()
        self.audits = AuditRepository()
        self.feedback_items = FeedbackRepository()
        self.notifications = NotificationRepository()
        self.event_store = EventRepository()
        self.analytics = AnalyticsService(self.event_store)
        self.identity = IdentityService(
            self.users, self.analytics.record, self.clock, self.audits
        )
        self.catalog = CatalogService(
            self.points,
            self.analytics.record,
            self.clock,
            actor_roles=self._roles_for,
        )
        self.content = ContentService(
            self.cards,
            self.points,
            self.audits,
            self._roles_for,
            self.analytics.record,
            self.clock,
        )
        self.review = ReviewService(self.plans, self.analytics.record, self.clock)
        self.learning = LearningService(
            self.records,
            self.cards,
            self.review,
            self.analytics.record,
            self.clock,
        )
        self.delivery = CardDeliveryService(self.content.list_published_cards, self.clock)
        self.wechat = InMemoryWechatAdapter()
        self.notification = NotificationService(
            self.users,
            self.review,
            self.notifications,
            self.wechat,
            self.analytics.record,
            self.clock,
        )
        self.feedback = FeedbackService(
            self.feedback_items,
            self.cards,
            self._roles_for,
            self.analytics.record,
            self.clock,
        )

    # API gateway: user-facing operations
    def create_session(self, wechat_open_id: str, client_version: str = "dev") -> User:
        return self.identity.create_session(wechat_open_id, client_version)

    def complete_onboarding(self, user_id: str, goal: str = "CAPM") -> User:
        return self.identity.complete_onboarding(user_id, goal)

    def get_learning_entry(self, user_id: str, at=None) -> dict:
        user = self._user(user_id)
        require(user.onboarding_completed, "请先完成新手引导")
        now = at or self.clock()
        due = self.review.get_due_reviews(user_id, now, user.review_limit)
        if due:
            point_ids = [plan.knowledge_point_id for plan in due]
            cards = self.delivery.get_card_sequence(
                min(len(point_ids), user.review_limit), point_ids
            )
            self.analytics.record(
                self._event(
                    "review_entered",
                    now,
                    {"user_id": user_id, "due_count": len(due)},
                )
            )
            return {"mode": "REVIEW", "tasks": due, "cards": cards}
        known = self.learning.known_knowledge_points(user_id)
        cards = self.delivery.get_card_sequence(user.new_card_limit, exclude_knowledge_point_ids=known)
        self.analytics.record(
            self._event(
                "learning_entry_opened",
                now,
                {"user_id": user_id, "mode": "NEW", "card_count": len(cards)},
            )
        )
        if cards:
            self.analytics.record(
                self._event(
                    "card_displayed",
                    now,
                    {"user_id": user_id, "card_version_id": cards[0].id},
                )
            )
        return {"mode": "NEW", "tasks": [], "cards": cards}

    def complete_card(self, user_id: str, session_id: str, card_version_id: str) -> bool:
        self._require_learner(user_id)
        return self.learning.complete_card(user_id, session_id, card_version_id)

    def submit_rating(
        self,
        user_id: str,
        session_id: str,
        card_version_id: str,
        rating,
        idempotency_key: str,
        client_version: str = "dev",
        correction_of: Optional[str] = None,
        occurred_at=None,
    ):
        self._require_learner(user_id)
        return self.learning.submit_rating(
            user_id,
            session_id,
            card_version_id,
            rating,
            idempotency_key,
            client_version,
            correction_of,
            occurred_at,
        )

    # API gateway: settings and reminders
    def get_due_reviews(self, user_id: str, at=None):
        user = self._user(user_id)
        require(user.onboarding_completed, "请先完成新手引导")
        return self.review.get_due_reviews(user_id, at, user.review_limit)

    def get_study_settings(self, user_id: str):
        return self.identity.get_study_settings(user_id)

    def update_study_settings(self, user_id: str, **settings):
        return self.identity.update_study_settings(user_id, **settings)

    def request_subscription(self, user_id: str, authorized: bool):
        return self.identity.request_subscription(user_id, authorized)

    def create_daily_reminder(self, user_id: str, at=None):
        return self.notification.create_daily_summary(user_id, at)

    # API gateway: content backend operations
    def create_knowledge_point(self, actor_id: str, **data):
        return self.catalog.create_knowledge_point(actor_id, **data)

    def create_card_draft(self, actor_id: str, **data):
        return self.content.create_card_draft(actor_id, **data)

    def update_card_draft(self, actor_id: str, card_version_id: str, **fields):
        return self.content.update_card_draft(actor_id, card_version_id, **fields)

    def generate_card_draft(
        self, actor_id: str, knowledge_point_id: str, input_text: str, source: str, source_locator: str
    ):
        return self.content.generate_card_draft(
            actor_id, knowledge_point_id, input_text, source, source_locator
        )

    def submit_for_review(self, actor_id: str, card_version_id: str, request_id: str):
        return self.content.submit_for_review(actor_id, card_version_id, request_id)

    def approve_content(self, actor_id: str, card_version_id: str, reason: str, request_id: str):
        return self.content.approve(actor_id, card_version_id, reason, request_id)

    def reject_content(self, actor_id: str, card_version_id: str, reason: str, request_id: str):
        return self.content.reject(actor_id, card_version_id, reason, request_id)

    def publish_content(self, actor_id: str, card_version_id: str, request_id: str):
        return self.content.publish(actor_id, card_version_id, request_id)

    def unpublish_content(self, actor_id: str, card_version_id: str, reason: str, request_id: str):
        return self.content.unpublish(actor_id, card_version_id, reason, request_id)

    def restore_content(self, actor_id: str, card_version_id: str, reason: str, request_id: str):
        return self.content.restore(actor_id, card_version_id, reason, request_id)

    def list_versions(self, card_id: str):
        return sorted(self.content.list_versions(card_id), key=lambda item: item.version)

    def list_audit_events(self, object_id: Optional[str] = None):
        if object_id is None:
            return list(self.audits.items)
        return self.audits.for_object(object_id)

    def list_content_feedback(self):
        return self.feedback_items.all()

    def resolve_content_feedback(self, actor_id: str, feedback_id: str, resolution: str):
        return self.feedback.resolve(actor_id, feedback_id, resolution)

    def submit_content_feedback(self, user_id: str, card_version_id: str, feedback_type, description=None):
        return self.feedback.submit(user_id, card_version_id, feedback_type, description)

    def _roles_for(self, user_id: str):
        user = self.users.get(user_id)
        return user.roles if user else ()

    def _user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("用户不存在")
        return user

    def _require_learner(self, user_id: str) -> User:
        user = self._user(user_id)
        require(user.onboarding_completed, "请先完成新手引导")
        return user

    @staticmethod
    def _event(name, occurred_at, payload):
        from .models import DomainEvent

        return DomainEvent(name, occurred_at, payload)

    def create_staff_session(self, wechat_open_id: str, roles) -> User:
        """Development bootstrap helper; production should use an IAM service."""
        user = self.create_session(wechat_open_id, "admin")
        user.roles = tuple(dict.fromkeys(roles))
        self.users.save(user)
        return user
