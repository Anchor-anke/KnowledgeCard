"""Daily due-review summaries and a provider-neutral WeChat adapter."""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from .core import Clock, new_id
from .models import DomainEvent, NotificationTask
from .repositories import NotificationRepository


class InMemoryWechatAdapter:
    def __init__(self):
        self.sent = []
        self.fail_next = False

    def send_review_summary(self, user, due_count: int) -> None:
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("微信服务暂时不可用")
        self.sent.append((user.id, due_count))


class NotificationService:
    def __init__(
        self,
        users,
        review_service,
        notifications: NotificationRepository,
        wechat_adapter,
        events=None,
        clock: Optional[Clock] = None,
    ):
        from .core import utc_now

        self.users = users
        self.review_service = review_service
        self.notifications = notifications
        self.wechat = wechat_adapter
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now

    def create_daily_summary(self, user_id: str, at=None) -> NotificationTask:
        user = self.users.get(user_id)
        if user is None:
            raise ValueError("用户不存在")
        now = at or self.clock()
        local_date = now.astimezone(ZoneInfo(user.timezone)).date().isoformat()
        existing = self.notifications.get(user_id, local_date)
        if existing is not None and not (
            existing.status == "FAILED"
            or (existing.status == "SKIPPED_UNAUTHORIZED" and user.subscription_authorized)
        ):
            return existing
        due = self.review_service.get_due_reviews(user_id, now)
        if not user.subscription_authorized:
            task = NotificationTask(
                id=new_id("notify"),
                user_id=user_id,
                local_date=local_date,
                due_count=len(due),
                created_at=now,
                status="SKIPPED_UNAUTHORIZED",
            )
            self.notifications.save(task)
            return task
        try:
            self.wechat.send_review_summary(user, len(due))
            status = "SENT"
            failure_reason = None
        except Exception as exc:
            status = "FAILED"
            failure_reason = str(exc)
        task = NotificationTask(
            id=new_id("notify"),
            user_id=user_id,
            local_date=local_date,
            due_count=len(due),
            created_at=now,
            status=status,
            failure_reason=failure_reason,
        )
        self.notifications.save(task)
        self.events(
            DomainEvent(
                "review_reminder_sent" if status == "SENT" else "review_reminder_failed",
                now,
                {"user_id": user_id, "due_count": len(due), "status": status},
            )
        )
        return task
