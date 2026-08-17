"""CAPM examination and knowledge-point catalogue."""

from typing import Optional

from .core import AuthorizationError, Clock, NotFoundError, new_id, require
from .models import DomainEvent, KnowledgePoint, Role
from .repositories import KnowledgePointRepository


class CatalogService:
    def __init__(
        self,
        points: KnowledgePointRepository,
        events=None,
        clock: Optional[Clock] = None,
        actor_roles=None,
    ):
        from .core import utc_now

        self.points = points
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now
        self.actor_roles = actor_roles or (lambda actor_id: ())

    def create_knowledge_point(
        self,
        actor_id: str,
        exam_id: str,
        domain: str,
        topic: str,
        chapter: str,
        objective: str,
        difficulty: str,
    ) -> KnowledgePoint:
        self._require_role(actor_id, Role.EDITOR)
        for value, label in (
            (exam_id, "考试"),
            (domain, "领域"),
            (topic, "主题"),
            (chapter, "章节"),
            (objective, "知识目标"),
            (difficulty, "难度"),
        ):
            require(bool(value.strip()), "{}不能为空".format(label))
        require(exam_id == "CAPM", "MVP 目前只允许 CAPM 考试")
        item = KnowledgePoint(
            id=new_id("kp"),
            exam_id=exam_id,
            domain=domain,
            topic=topic,
            chapter=chapter,
            objective=objective,
            difficulty=difficulty,
            created_by=actor_id,
            created_at=self.clock(),
        )
        self.points.save(item)
        return item

    def _require_role(self, actor_id: str, role: Role) -> None:
        if role not in tuple(self.actor_roles(actor_id)):
            raise AuthorizationError("当前用户没有 {} 权限".format(role.value))

    def get(self, point_id: str) -> KnowledgePoint:
        item = self.points.get(point_id)
        if item is None:
            raise NotFoundError("知识点不存在")
        return item
