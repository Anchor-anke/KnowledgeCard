"""Content production workflow, AI draft generation and publication gates."""

from dataclasses import replace
from typing import Dict, List, Optional

from .core import (
    AuthorizationError,
    Clock,
    ConflictError,
    NotFoundError,
    ValidationError,
    new_id,
    require,
)
from .models import (
    AuditEvent,
    CardVersion,
    ContentStatus,
    DomainEvent,
    KnowledgePoint,
    Role,
)
from .repositories import AuditRepository, CardRepository


class DeterministicAIGateway:
    """Offline AI adapter used by the MVP until a provider is configured."""

    model_version = "offline-template-v1"

    def generate(self, knowledge_point: KnowledgePoint, input_text: str) -> Dict[str, str]:
        subject = input_text.strip() or knowledge_point.objective
        return {
            "title": knowledge_point.objective,
            "conclusion": "CAPM 中，{}。".format(subject),
            "explanation": "先识别知识目标，再根据项目上下文选择合适的过程或工具。",
            "example": "示例：将该知识目标放入一个具体项目场景，说明何时使用它。",
            "recall_prompt": "请回忆：{} 的核心要点是什么？".format(subject),
            "reference_answer": "围绕 {} 说明定义、适用场景和关键注意事项。".format(subject),
        }


class ContentService:
    ALLOWED_TRANSITIONS = {
        ContentStatus.DRAFT: (ContentStatus.IN_REVIEW,),
        ContentStatus.IN_REVIEW: (ContentStatus.REJECTED, ContentStatus.APPROVED),
        ContentStatus.REJECTED: (ContentStatus.DRAFT,),
        ContentStatus.APPROVED: (ContentStatus.PUBLISHED,),
        ContentStatus.PUBLISHED: (ContentStatus.UNPUBLISHED,),
        ContentStatus.UNPUBLISHED: (ContentStatus.PUBLISHED, ContentStatus.ARCHIVED),
    }

    def __init__(
        self,
        cards: CardRepository,
        points,
        audits: AuditRepository,
        actor_roles,
        events=None,
        clock: Optional[Clock] = None,
        ai_gateway=None,
    ):
        from .core import utc_now

        self.cards = cards
        self.points = points
        self.audits = audits
        self.actor_roles = actor_roles
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now
        self.ai_gateway = ai_gateway or DeterministicAIGateway()

    def create_card_draft(
        self,
        actor_id: str,
        knowledge_point_id: str,
        title: str,
        conclusion: str,
        explanation: str,
        example: str,
        recall_prompt: str,
        reference_answer: str,
        source: str,
        source_locator: str,
        ai_generated: bool = False,
        ai_model_version: Optional[str] = None,
    ) -> CardVersion:
        self._require_role(actor_id, Role.EDITOR)
        point = self._get_point(knowledge_point_id)
        self._validate_card_fields(
            title,
            conclusion,
            explanation,
            example,
            recall_prompt,
            reference_answer,
            source,
            source_locator,
        )
        now = self.clock()
        item = CardVersion(
            id=new_id("cardv"),
            card_id=new_id("card"),
            knowledge_point_id=point.id,
            version=1,
            title=title.strip(),
            conclusion=conclusion.strip(),
            explanation=explanation.strip(),
            example=example.strip(),
            recall_prompt=recall_prompt.strip(),
            reference_answer=reference_answer.strip(),
            source=source.strip(),
            source_locator=source_locator.strip(),
            created_by=actor_id,
            created_at=now,
            ai_generated=ai_generated,
            ai_model_version=ai_model_version,
        )
        self.cards.save(item)
        self.events(DomainEvent("content_draft_created", now, {"card_version_id": item.id}))
        return item

    def create_card_revision(self, actor_id: str, card_id: str) -> CardVersion:
        self._require_role(actor_id, Role.EDITOR)
        previous = self._get_latest_card(card_id)
        require(
            previous.status in (ContentStatus.PUBLISHED, ContentStatus.UNPUBLISHED),
            "只有已发布或已下架版本可以创建修订",
        )
        now = self.clock()
        item = replace(
            previous,
            id=new_id("cardv"),
            version=previous.version + 1,
            created_by=actor_id,
            created_at=now,
            status=ContentStatus.DRAFT,
            reviewed_by=None,
            reviewed_at=None,
            review_reason=None,
            published_by=None,
            published_at=None,
            unpublished_reason=None,
        )
        self.cards.save(item)
        self.events(DomainEvent("content_draft_created", now, {"card_version_id": item.id}))
        return item

    def update_card_draft(self, actor_id: str, card_version_id: str, **fields) -> CardVersion:
        self._require_role(actor_id, Role.EDITOR)
        item = self._get_card(card_version_id)
        require(item.created_by == actor_id, "只能编辑自己创建的草稿")
        require(
            item.status in (ContentStatus.DRAFT, ContentStatus.REJECTED),
            "当前状态不能编辑，已发布版本必须创建新修订",
        )
        allowed = {
            "title",
            "conclusion",
            "explanation",
            "example",
            "recall_prompt",
            "reference_answer",
            "source",
            "source_locator",
        }
        unknown = set(fields) - allowed
        require(not unknown, "不支持修改字段: {}".format(", ".join(sorted(unknown))))
        values = {key: getattr(item, key) for key in allowed}
        values.update(fields)
        self._validate_card_fields(**values)
        for key, value in fields.items():
            setattr(item, key, value.strip() if isinstance(value, str) else value)
        self.cards.save(item)
        return item

    def generate_card_draft(
        self, actor_id: str, knowledge_point_id: str, input_text: str, source: str, source_locator: str
    ) -> CardVersion:
        self._require_role(actor_id, Role.EDITOR)
        point = self._get_point(knowledge_point_id)
        output = self.ai_gateway.generate(point, input_text)
        item = self.create_card_draft(
            actor_id=actor_id,
            knowledge_point_id=knowledge_point_id,
            source=source,
            source_locator=source_locator,
            ai_generated=True,
            ai_model_version=self.ai_gateway.model_version,
            **output
        )
        self.events(
            DomainEvent(
                "ai_generation_completed",
                self.clock(),
                {"card_version_id": item.id, "model_version": self.ai_gateway.model_version},
            )
        )
        return item

    def submit_for_review(self, actor_id: str, card_version_id: str, request_id: str) -> CardVersion:
        self._require_role(actor_id, Role.EDITOR)
        return self._transition(
            actor_id, card_version_id, ContentStatus.IN_REVIEW, None, request_id
        )

    def approve(self, actor_id: str, card_version_id: str, reason: str, request_id: str) -> CardVersion:
        self._require_role(actor_id, Role.REVIEWER)
        item = self._get_card(card_version_id)
        require(item.status == ContentStatus.IN_REVIEW, "只有审核中的版本可以审核")
        require(item.created_by != actor_id, "不能审核自己创建的内容")
        require(bool(reason.strip()), "审核通过必须填写审核意见")
        item.reviewed_by = actor_id
        item.reviewed_at = self.clock()
        item.review_reason = reason.strip()
        self.cards.save(item)
        return self._transition(
            actor_id, card_version_id, ContentStatus.APPROVED, reason, request_id
        )

    def reject(self, actor_id: str, card_version_id: str, reason: str, request_id: str) -> CardVersion:
        self._require_role(actor_id, Role.REVIEWER)
        item = self._get_card(card_version_id)
        require(item.status == ContentStatus.IN_REVIEW, "只有审核中的版本可以审核")
        require(item.created_by != actor_id, "不能审核自己创建的内容")
        require(bool(reason.strip()), "驳回必须填写原因")
        item.reviewed_by = actor_id
        item.reviewed_at = self.clock()
        item.review_reason = reason.strip()
        self.cards.save(item)
        return self._transition(
            actor_id, card_version_id, ContentStatus.REJECTED, reason, request_id
        )

    def publish(self, actor_id: str, card_version_id: str, request_id: str) -> CardVersion:
        self._require_role(actor_id, Role.PUBLISHER)
        item = self._get_card(card_version_id)
        require(item.status == ContentStatus.APPROVED, "只有审核通过版本可以发布")
        for previous in self.cards.versions_for_point(item.knowledge_point_id):
            if previous.card_id == item.card_id and previous.status == ContentStatus.PUBLISHED:
                previous.status = ContentStatus.UNPUBLISHED
                previous.unpublished_reason = "新版本发布"
                self.cards.save(previous)
                self._audit(
                    actor_id, previous, ContentStatus.PUBLISHED, ContentStatus.UNPUBLISHED,
                    "新版本发布", request_id
                )
        item.published_by = actor_id
        item.published_at = self.clock()
        self.cards.save(item)
        return self._transition(
            actor_id, card_version_id, ContentStatus.PUBLISHED, "发布", request_id
        )

    def unpublish(self, actor_id: str, card_version_id: str, reason: str, request_id: str) -> CardVersion:
        self._require_role(actor_id, Role.PUBLISHER)
        require(bool(reason.strip()), "下架必须填写原因")
        return self._transition(
            actor_id, card_version_id, ContentStatus.UNPUBLISHED, reason, request_id
        )

    def restore(self, actor_id: str, card_version_id: str, reason: str, request_id: str) -> CardVersion:
        self._require_role(actor_id, Role.PUBLISHER)
        require(bool(reason.strip()), "恢复必须填写原因")
        item = self._get_card(card_version_id)
        require(item.status == ContentStatus.UNPUBLISHED, "只有已下架版本可以恢复")
        for previous in self.cards.versions_for_point(item.knowledge_point_id):
            if previous.card_id == item.card_id and previous.status == ContentStatus.PUBLISHED:
                previous.status = ContentStatus.UNPUBLISHED
                self.cards.save(previous)
        return self._transition(
            actor_id, card_version_id, ContentStatus.PUBLISHED, reason, request_id
        )

    def list_published_cards(self, knowledge_point_ids=None) -> List[CardVersion]:
        allowed = set(knowledge_point_ids) if knowledge_point_ids is not None else None
        return [
            item
            for item in self.cards.published()
            if allowed is None or item.knowledge_point_id in allowed
        ]

    def list_versions(self, card_id: str) -> List[CardVersion]:
        return [
            item
            for item in self.cards.items.values()
            if item.card_id == card_id
        ]

    def _transition(self, actor_id, card_version_id, target, reason, request_id):
        require(
            isinstance(request_id, str) and bool(request_id.strip()),
            "请求编号不能为空",
        )
        item = self._get_card(card_version_id)
        allowed = self.ALLOWED_TRANSITIONS.get(item.status, ())
        require(target in allowed, "{} 不能转换为 {}".format(item.status.value, target.value))
        previous = item.status
        item.status = target
        if target == ContentStatus.UNPUBLISHED:
            item.unpublished_reason = reason
        self.cards.save(item)
        self._audit(actor_id, item, previous, target, reason, request_id)
        event_name = {
            ContentStatus.IN_REVIEW: "content_submitted_for_review",
            ContentStatus.APPROVED: "content_approved",
            ContentStatus.REJECTED: "content_rejected",
            ContentStatus.PUBLISHED: "content_published",
            ContentStatus.UNPUBLISHED: "content_unpublished",
        }.get(target)
        if event_name:
            self.events(DomainEvent(event_name, self.clock(), {"card_version_id": item.id}))
        return item

    def _audit(self, actor_id, item, from_status, to_status, reason, request_id):
        role = next(iter(self.actor_roles(actor_id)), None)
        self.audits.save(
            AuditEvent(
                id=new_id("audit"),
                actor_id=actor_id,
                actor_role=role,
                object_type="CARD_VERSION",
                object_id=item.id,
                from_status=from_status.value if from_status else None,
                to_status=to_status.value if to_status else None,
                reason=reason,
                request_id=request_id,
                occurred_at=self.clock(),
            )
        )

    def _require_role(self, actor_id: str, role: Role) -> None:
        if role not in tuple(self.actor_roles(actor_id)):
            raise AuthorizationError("当前用户没有 {} 权限".format(role.value))

    def _get_card(self, card_version_id: str) -> CardVersion:
        item = self.cards.get(card_version_id)
        if item is None:
            raise NotFoundError("卡片版本不存在")
        return item

    def _get_latest_card(self, card_id: str) -> CardVersion:
        versions = self.list_versions(card_id)
        if not versions:
            raise NotFoundError("卡片不存在")
        return sorted(versions, key=lambda item: item.version)[-1]

    def _get_point(self, point_id: str) -> KnowledgePoint:
        point = self.points.get(point_id)
        if point is None:
            raise NotFoundError("知识点不存在")
        return point

    @staticmethod
    def _validate_card_fields(
        title,
        conclusion,
        explanation,
        example,
        recall_prompt,
        reference_answer,
        source,
        source_locator,
    ):
        fields = (
            (title, "标题"),
            (conclusion, "结论"),
            (explanation, "解释"),
            (example, "例子"),
            (recall_prompt, "回忆提示"),
            (reference_answer, "参考答案"),
            (source, "来源"),
            (source_locator, "来源定位"),
        )
        for value, label in fields:
            require(isinstance(value, str) and bool(value.strip()), "{}不能为空".format(label))
