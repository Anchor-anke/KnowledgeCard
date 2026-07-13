"""Identity, onboarding, study settings and server-side role checks."""

import re
from typing import Callable, Optional
from .models import AuditEvent

from .core import Clock, AuthorizationError, NotFoundError, ValidationError, new_id, require
from .models import DomainEvent, Role, User
from .repositories import UserRepository


EventSink = Callable[[DomainEvent], None]


class IdentityService:
    def __init__(
        self,
        users: UserRepository,
        events: Optional[EventSink] = None,
        clock: Optional[Clock] = None,
        audits=None,
    ):
        from .core import utc_now

        self.users = users
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now
        self.audits = audits

    def create_session(self, wechat_open_id: str, client_version: str) -> User:
        require(bool(wechat_open_id), "微信登录凭证不能为空")
        now = self.clock()
        user = self.users.find_by_wechat_id(wechat_open_id)
        first_login = user is None
        if user is None:
            user = User(
                id=new_id("usr"),
                wechat_open_id=wechat_open_id,
                created_at=now,
                last_active_at=now,
            )
        else:
            user.last_active_at = now
        self.users.save(user)
        self.events(
            DomainEvent(
                "login_succeeded",
                now,
                {
                    "user_id": user.id,
                    "first_login": first_login,
                    "client_version": client_version,
                },
            )
        )
        return user

    def complete_onboarding(self, user_id: str, goal: str) -> User:
        user = self._get_user(user_id)
        require(goal == "CAPM", "MVP 目前只支持 CAPM 学习目标")
        user.goal = goal
        user.onboarding_completed = True
        user.last_active_at = self.clock()
        self.users.save(user)
        self._audit(user, "onboarding_completed", "引导完成")
        self.events(
            DomainEvent(
                "onboarding_completed",
                self.clock(),
                {"user_id": user.id, "goal": goal},
            )
        )
        return user

    def request_subscription(self, user_id: str, authorized: bool) -> User:
        user = self._get_user(user_id)
        user.subscription_authorized = authorized
        self.users.save(user)
        self._audit(
            user,
            "subscription_authorized" if authorized else "subscription_rejected",
            "订阅消息授权状态变更",
        )
        self.events(
            DomainEvent(
                "subscription_authorized" if authorized else "subscription_rejected",
                self.clock(),
                {"user_id": user.id},
            )
        )
        return user

    def get_study_settings(self, user_id: str) -> dict:
        user = self._get_user(user_id)
        return {
            "new_card_limit": user.new_card_limit,
            "review_limit": user.review_limit,
            "reminder_time": user.reminder_time,
            "timezone": user.timezone,
            "subscription_authorized": user.subscription_authorized,
        }

    def update_study_settings(
        self,
        user_id: str,
        new_card_limit: Optional[int] = None,
        review_limit: Optional[int] = None,
        reminder_time: Optional[str] = None,
    ) -> User:
        user = self._get_user(user_id)
        if new_card_limit is not None:
            require(0 < new_card_limit <= 100, "每日新卡上限必须在 1 到 100 之间")
            user.new_card_limit = new_card_limit
        if review_limit is not None:
            require(0 < review_limit <= 200, "每日复习上限必须在 1 到 200 之间")
            user.review_limit = review_limit
        if reminder_time is not None:
            require(
                re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", reminder_time) is not None,
                "提醒时间必须使用 HH:MM 格式",
            )
            user.reminder_time = reminder_time
        self.users.save(user)
        self._audit(user, "study_settings_updated", "学习和提醒设置变更")
        return user

    def require_role(self, actor_id: str, role: Role) -> User:
        user = self._get_user(actor_id)
        if role not in user.roles:
            raise AuthorizationError("当前用户没有 {} 权限".format(role.value))
        return user

    def _get_user(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("用户不存在")
        return user

    def _audit(self, user: User, operation: str, reason: str) -> None:
        if self.audits is None:
            return
        role = user.roles[0] if user.roles else None
        self.audits.save(
            AuditEvent(
                id=new_id("audit"),
                actor_id=user.id,
                actor_role=role,
                object_type="USER",
                object_id=user.id,
                from_status=None,
                to_status=operation,
                reason=reason,
                request_id=new_id("req"),
                occurred_at=self.clock(),
            )
        )

