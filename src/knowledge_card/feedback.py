"""User content feedback with short-window deduplication."""

from datetime import timedelta
from typing import Optional

from .core import AuthorizationError, Clock, NotFoundError, ValidationError, new_id, require
from .models import ContentFeedback, DomainEvent, FeedbackStatus, FeedbackType, Role
from .repositories import FeedbackRepository


class FeedbackService:
    def __init__(self, feedback: FeedbackRepository, cards, actor_roles, events=None, clock: Optional[Clock] = None):
        from .core import utc_now

        self.feedback = feedback
        self.cards = cards
        self.actor_roles = actor_roles
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now

    def submit(
        self,
        user_id: str,
        card_version_id: str,
        feedback_type: FeedbackType,
        description: Optional[str] = None,
        severity: str = "NORMAL",
    ) -> ContentFeedback:
        try:
            feedback_type = (
                feedback_type
                if isinstance(feedback_type, FeedbackType)
                else FeedbackType(feedback_type)
            )
        except ValueError:
            raise ValidationError("无效的内容反馈类型")
        card = self.cards.get(card_version_id)
        if card is None:
            raise NotFoundError("卡片版本不存在")
        now = self.clock()
        for item in self.feedback.all():
            if (
                item.user_id == user_id
                and item.card_version_id == card_version_id
                and item.feedback_type == feedback_type
                and now - item.created_at <= timedelta(hours=24)
                and item.status != FeedbackStatus.WITHDRAWN
            ):
                return item
        item = ContentFeedback(
            id=new_id("feedback"),
            user_id=user_id,
            card_id=card.card_id,
            knowledge_point_id=card.knowledge_point_id,
            card_version_id=card.id,
            feedback_type=feedback_type,
            description=description.strip() if description else None,
            status=FeedbackStatus.OPEN,
            severity=severity,
            created_at=now,
        )
        self.feedback.save(item)
        self.events(
            DomainEvent(
                "content_feedback_submitted",
                now,
                {"feedback_id": item.id, "card_version_id": card.id, "severity": severity},
            )
        )
        return item

    def resolve(self, actor_id: str, feedback_id: str, resolution: str) -> ContentFeedback:
        if Role.REVIEWER not in tuple(self.actor_roles(actor_id)):
            raise AuthorizationError("只有审核员可以处理内容反馈")
        item = self.feedback.get(feedback_id)
        if item is None:
            raise NotFoundError("反馈不存在")
        require(bool(resolution.strip()), "处理结论不能为空")
        item.status = FeedbackStatus.RESOLVED
        item.resolved_by = actor_id
        item.resolution = resolution.strip()
        self.feedback.save(item)
        self.events(
            DomainEvent(
                "content_feedback_resolved",
                self.clock(),
                {"feedback_id": feedback_id, "resolved_by": actor_id},
            )
        )
        return item

