"""Published card delivery and immutable learning facts."""

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Set, Tuple

from .core import Clock, ConflictError, NotFoundError, ValidationError, new_id, require
from .models import CardVersion, ContentStatus, DomainEvent, LearningRecord, LearningStage, Rating
from .repositories import LearningRecordRepository


@dataclass(frozen=True)
class CardView:
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


class CardDeliveryService:
    """The only user-facing card read path."""

    def __init__(self, published_cards: Callable, clock: Optional[Clock] = None):
        self.published_cards = published_cards
        self.clock = clock

    def get_card_sequence(
        self,
        limit: int,
        knowledge_point_ids: Optional[Iterable[str]] = None,
        exclude_knowledge_point_ids: Optional[Iterable[str]] = None,
    ) -> List[CardView]:
        require(0 < limit <= 100, "卡片数量必须在 1 到 100 之间")
        allowed = set(knowledge_point_ids) if knowledge_point_ids is not None else None
        excluded = set(exclude_knowledge_point_ids or ())
        cards = self.published_cards(allowed)
        cards = [
            card
            for card in cards
            if card.knowledge_point_id not in excluded
            and card.status == ContentStatus.PUBLISHED
        ]
        return [self._view(card) for card in cards[:limit]]

    @staticmethod
    def _view(card: CardVersion) -> CardView:
        return CardView(
            id=card.id,
            card_id=card.card_id,
            knowledge_point_id=card.knowledge_point_id,
            version=card.version,
            title=card.title,
            conclusion=card.conclusion,
            explanation=card.explanation,
            example=card.example,
            recall_prompt=card.recall_prompt,
            reference_answer=card.reference_answer,
            source=card.source,
            source_locator=card.source_locator,
        )


class LearningService:
    def __init__(
        self,
        records: LearningRecordRepository,
        cards,
        review_service,
        events=None,
        clock: Optional[Clock] = None,
    ):
        from .core import utc_now

        self.records = records
        self.cards = cards
        self.review_service = review_service
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now
        self._completed: Set[Tuple[str, str, str]] = set()

    def complete_card(self, user_id: str, session_id: str, card_version_id: str) -> bool:
        card = self.cards.get(card_version_id)
        if card is None:
            raise NotFoundError("卡片版本不存在")
        require(card.status == ContentStatus.PUBLISHED, "只有已发布卡片可以学习")
        require(bool(session_id), "学习会话不能为空")
        key = (user_id, session_id, card_version_id)
        if key in self._completed:
            return False
        self._completed.add(key)
        self.events(
            DomainEvent(
                "card_completed",
                self.clock(),
                {
                    "user_id": user_id,
                    "session_id": session_id,
                    "card_version_id": card_version_id,
                },
            )
        )
        return True

    def submit_rating(
        self,
        user_id: str,
        session_id: str,
        card_version_id: str,
        rating: Rating,
        idempotency_key: str,
        client_version: str,
        correction_of: Optional[str] = None,
        occurred_at=None,
    ) -> LearningRecord:
        require(bool(idempotency_key), "幂等键不能为空")
        require(bool(session_id), "学习会话不能为空")
        if not isinstance(rating, Rating):
            try:
                rating = Rating(rating)
            except ValueError:
                raise ValidationError("无效的记忆自评")
        existing = self.records.find_by_idempotency(user_id, idempotency_key)
        if existing is not None:
            same_request = (
                existing.card_version_id == card_version_id
                and existing.session_id == session_id
                and existing.rating == rating
                and existing.correction_of == correction_of
            )
            if not same_request:
                raise ConflictError("幂等键已经绑定到另一条学习请求")
            return existing
        card = self.cards.get(card_version_id)
        if card is None:
            raise NotFoundError("卡片版本不存在")
        require(card.status == ContentStatus.PUBLISHED, "只有已发布卡片可以学习")
        completion_key = (user_id, session_id, card_version_id)
        if correction_of is None and completion_key not in self._completed:
            raise ConflictError("请先完成卡片，再提交记忆自评")
        if correction_of is not None:
            original = self.records.get(correction_of)
            if original is None or original.user_id != user_id:
                raise ValidationError("待修正的学习记录不存在")
            require(
                original.card_version_id == card_version_id,
                "修正记录必须关联同一张卡片版本",
            )
        server_time = self.clock()
        if occurred_at is not None:
            require(
                getattr(occurred_at, "tzinfo", None) is not None
                and occurred_at.utcoffset() is not None,
                "学习发生时间必须包含时区",
            )
            try:
                drift_seconds = abs((occurred_at - server_time).total_seconds())
            except TypeError as exc:
                raise ValidationError("学习发生时间必须使用兼容的时区") from exc
            require(drift_seconds <= 300, "学习发生时间与服务器时间相差过大")
        # Scheduling must use server time. The optional client timestamp is only
        # accepted as a small clock-skew check and is never trusted for review.
        at = server_time
        stage = self.review_service.current_stage(user_id, card.knowledge_point_id)
        record = LearningRecord(
            id=new_id("learn"),
            user_id=user_id,
            card_id=card.card_id,
            knowledge_point_id=card.knowledge_point_id,
            card_version_id=card.id,
            session_id=session_id,
            stage=stage,
            rating=rating,
            occurred_at=at,
            client_version=client_version,
            idempotency_key=idempotency_key,
            correction_of=correction_of,
        )
        self.records.save(record)
        self.review_service.schedule(user_id, card.knowledge_point_id, rating, at)
        self.events(
            DomainEvent(
                "rating_corrected" if correction_of else "rating_submitted",
                at,
                {
                    "user_id": user_id,
                    "knowledge_point_id": card.knowledge_point_id,
                    "card_version_id": card.id,
                    "rating": rating.value,
                    "record_id": record.id,
                    "correction_of": correction_of,
                },
            )
        )
        return record

    def history(self, user_id: str) -> List[LearningRecord]:
        return self.records.for_user(user_id)

    def known_knowledge_points(self, user_id: str) -> Set[str]:
        return {record.knowledge_point_id for record in self.records.for_user(user_id)}
