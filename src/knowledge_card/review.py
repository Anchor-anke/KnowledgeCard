"""Transparent, versioned interval-review rules."""

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

from .core import Clock, DomainError, NotFoundError, new_id
from .models import DomainEvent, LearningStage, Rating, ReviewPlan
from .repositories import ReviewPlanRepository


@dataclass(frozen=True)
class ReviewAlgorithmConfig:
    version: str = "mvp-v1"
    first_review_minutes: int = 10
    vague_interval_days: int = 1
    remembered_intervals_days: tuple = (3, 7, 14, 30, 60)
    max_interval_days: int = 120


@dataclass(frozen=True)
class ScheduleResult:
    next_state: ReviewPlan
    reason: str


def calculate_next_review(
    current_state: Optional[ReviewPlan],
    rating: Rating,
    reviewed_at,
    algorithm_config: ReviewAlgorithmConfig,
) -> ScheduleResult:
    """Calculate a new state without mutating the input state."""

    previous = current_state
    previous_consecutive = previous.consecutive_remembered if previous else 0
    previous_stage = previous.stage if previous else LearningStage.NEW
    if rating == Rating.FORGOT:
        return ScheduleResult(
            _state(
                previous,
                LearningStage.LEARNING,
                reviewed_at + timedelta(minutes=algorithm_config.first_review_minutes),
                0,
                rating,
                0,
                algorithm_config,
                reviewed_at,
            ),
            "忘了：回到学习阶段并在 {} 分钟后复习".format(
                algorithm_config.first_review_minutes
            ),
        )
    if rating == Rating.VAGUE:
        return ScheduleResult(
            _state(
                previous,
                LearningStage.CONSOLIDATING,
                reviewed_at + timedelta(days=algorithm_config.vague_interval_days),
                float(algorithm_config.vague_interval_days),
                rating,
                0,
                algorithm_config,
                reviewed_at,
            ),
            "模糊：保持短间隔，{} 天后复习".format(algorithm_config.vague_interval_days),
        )

    consecutive = previous_consecutive + 1
    intervals = algorithm_config.remembered_intervals_days
    if consecutive <= len(intervals):
        interval_days = float(intervals[consecutive - 1])
    else:
        prior_interval = previous.interval_days if previous else float(intervals[-1])
        interval_days = min(
            max(prior_interval * 2, float(intervals[-1])),
            float(algorithm_config.max_interval_days),
        )
    stage = LearningStage.STABLE if consecutive >= 3 else LearningStage.CONSOLIDATING
    return ScheduleResult(
        _state(
            previous,
            stage,
            reviewed_at + timedelta(days=interval_days),
            interval_days,
            rating,
            consecutive,
            algorithm_config,
            reviewed_at,
        ),
        "记住了：连续记住 {} 次，{} 天后复习".format(consecutive, int(interval_days)),
    )


def _state(
    previous,
    stage,
    next_review_at,
    interval_days,
    rating,
    consecutive,
    config,
    reviewed_at,
):
    return ReviewPlan(
        user_id=previous.user_id if previous else "",
        knowledge_point_id=previous.knowledge_point_id if previous else "",
        stage=stage,
        next_review_at=next_review_at,
        last_reviewed_at=reviewed_at,
        last_rating=rating,
        consecutive_remembered=consecutive,
        interval_days=interval_days,
        algorithm_version=config.version,
        overdue=False,
        revision=(previous.revision + 1) if previous else 1,
        updated_at=reviewed_at,
    )


class ReviewService:
    def __init__(
        self,
        plans: ReviewPlanRepository,
        events=None,
        clock: Optional[Clock] = None,
        config: Optional[ReviewAlgorithmConfig] = None,
    ):
        from .core import utc_now

        self.plans = plans
        self.events = events or (lambda event: None)
        self.clock = clock or utc_now
        self.config = config or ReviewAlgorithmConfig()

    def schedule(self, user_id: str, knowledge_point_id: str, rating: Rating, reviewed_at) -> ReviewPlan:
        current = self.plans.get(user_id, knowledge_point_id)
        result = calculate_next_review(current, rating, reviewed_at, self.config)
        plan = result.next_state
        plan.user_id = user_id
        plan.knowledge_point_id = knowledge_point_id
        self.plans.save(plan)
        self.events(
            DomainEvent(
                "review_plan_updated",
                reviewed_at,
                {
                    "user_id": user_id,
                    "knowledge_point_id": knowledge_point_id,
                    "next_review_at": plan.next_review_at.isoformat(),
                    "algorithm_version": plan.algorithm_version,
                    "reason": result.reason,
                },
            )
        )
        return plan

    def get_due_reviews(self, user_id: str, at=None, limit: Optional[int] = None) -> List[ReviewPlan]:
        now = at or self.clock()
        due = [plan for plan in self.plans.for_user(user_id) if plan.next_review_at <= now]
        due.sort(key=lambda plan: plan.next_review_at)
        if limit is not None:
            due = due[:limit]
        for plan in due:
            plan.overdue = plan.next_review_at < now
            self.plans.save(plan)
        return due

    def get_plan(self, user_id: str, knowledge_point_id: str) -> ReviewPlan:
        plan = self.plans.get(user_id, knowledge_point_id)
        if plan is None:
            raise NotFoundError("该知识点还没有复习计划")
        return plan

    def current_stage(self, user_id: str, knowledge_point_id: str) -> LearningStage:
        plan = self.plans.get(user_id, knowledge_point_id)
        return plan.stage if plan else LearningStage.NEW

