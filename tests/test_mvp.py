import unittest
from datetime import datetime, timedelta, timezone

from knowledge_card import (
    ContentStatus,
    FeedbackType,
    KnowledgeCardApplication,
    Rating,
    Role,
)
from knowledge_card.core import AuthorizationError, ConflictError, ValidationError


class TestClock:
    def __init__(self):
        self.value = datetime(2026, 7, 13, 7, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.value

    def advance(self, **kwargs):
        self.value += timedelta(**kwargs)


class MvpTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = TestClock()
        self.app = KnowledgeCardApplication(self.clock)
        self.editor = self.app.create_staff_session("editor-openid", [Role.EDITOR])
        self.reviewer = self.app.create_staff_session("reviewer-openid", [Role.REVIEWER])
        self.publisher = self.app.create_staff_session("publisher-openid", [Role.PUBLISHER])
        self.user = self.app.create_session("learner-openid")
        self.app.complete_onboarding(self.user.id)
        self.point = self.app.create_knowledge_point(
            self.editor.id,
            exam_id="CAPM",
            domain="Project Management Fundamentals",
            topic="Project life cycle",
            chapter="Foundations",
            objective="区分项目和运营",
            difficulty="EASY",
        )

    def make_draft(self, title="项目与运营"):
        return self.app.content.create_card_draft(
            actor_id=self.editor.id,
            knowledge_point_id=self.point.id,
            title=title,
            conclusion="项目是临时的，运营是持续的。",
            explanation="项目有明确开始和结束，运营持续产生重复性结果。",
            example="实施一次系统升级是项目，日常客服是运营。",
            recall_prompt="项目和运营最关键的区别是什么？",
            reference_answer="项目是临时性工作，运营是持续性工作。",
            source="PMI CAPM ECO",
            source_locator="Domain 1 / objective 1",
        )

    def publish(self, draft):
        self.app.content.submit_for_review(self.editor.id, draft.id, "req-submit")
        self.app.content.approve(
            self.reviewer.id, draft.id, "事实和来源已核验", "req-approve"
        )
        return self.app.content.publish(self.publisher.id, draft.id, "req-publish")

    def test_first_learning_and_rating_are_idempotent(self):
        draft = self.make_draft()
        self.assertEqual(self.app.get_learning_entry(self.user.id)["cards"], [])
        self.publish(draft)
        entry = self.app.get_learning_entry(self.user.id)
        self.assertEqual(entry["mode"], "NEW")
        self.assertEqual(len(entry["cards"]), 1)
        card = entry["cards"][0]

        self.assertTrue(self.app.complete_card(self.user.id, "session-1", card.id))
        record = self.app.submit_rating(
            self.user.id, "session-1", card.id, Rating.FORGOT, "rating-1"
        )
        duplicate = self.app.submit_rating(
            self.user.id, "session-1", card.id, Rating.FORGOT, "rating-1"
        )
        self.assertEqual(record.id, duplicate.id)
        self.assertEqual(len(self.app.learning.history(self.user.id)), 1)
        plan = self.app.review.get_plan(self.user.id, self.point.id)
        self.assertEqual(plan.next_review_at, self.clock.value + timedelta(minutes=10))
        self.assertEqual(plan.algorithm_version, "mvp-v1")

    def test_due_review_has_priority_and_overdue_is_merged_by_knowledge_point(self):
        draft = self.make_draft()
        card = self.publish(draft)
        view = self.app.get_learning_entry(self.user.id)["cards"][0]
        self.app.complete_card(self.user.id, "s", view.id)
        self.app.submit_rating(self.user.id, "s", view.id, Rating.REMEMBERED, "r1")
        self.clock.advance(days=4)

        entry = self.app.get_learning_entry(self.user.id)
        self.assertEqual(entry["mode"], "REVIEW")
        self.assertEqual(len(entry["tasks"]), 1)
        self.assertTrue(entry["tasks"][0].overdue)
        self.assertEqual(len(entry["cards"]), 1)
        self.assertEqual(entry["cards"][0].id, card.id)

    def test_correction_is_a_new_immutable_record_and_reschedules(self):
        draft = self.make_draft()
        self.publish(draft)
        card = self.app.get_learning_entry(self.user.id)["cards"][0]
        self.app.complete_card(self.user.id, "s", card.id)
        first = self.app.submit_rating(self.user.id, "s", card.id, Rating.REMEMBERED, "r1")
        corrected = self.app.submit_rating(
            self.user.id,
            "s",
            card.id,
            Rating.FORGOT,
            "r2",
            correction_of=first.id,
        )
        self.assertNotEqual(first.id, corrected.id)
        self.assertEqual(corrected.correction_of, first.id)
        self.assertEqual(len(self.app.learning.history(self.user.id)), 2)
        self.assertEqual(
            self.app.review.get_plan(self.user.id, self.point.id).next_review_at,
            self.clock.value + timedelta(minutes=10),
        )

    def test_unreviewed_content_never_reaches_user(self):
        draft = self.make_draft()
        self.assertEqual(self.app.content.list_published_cards(), [])
        self.assertEqual(self.app.get_learning_entry(self.user.id)["cards"], [])
        self.app.content.submit_for_review(self.editor.id, draft.id, "req")
        self.assertEqual(self.app.get_learning_entry(self.user.id)["cards"], [])
        with self.assertRaises(ValidationError):
            self.app.complete_card(self.user.id, "session", draft.id)

    def test_catalog_creation_requires_editor_role(self):
        with self.assertRaises(AuthorizationError):
            self.app.create_knowledge_point(
                self.user.id,
                exam_id="CAPM",
                domain="d",
                topic="t",
                chapter="c",
                objective="o",
                difficulty="EASY",
            )

    def test_idempotency_key_cannot_be_reused_for_a_different_rating(self):
        draft = self.make_draft()
        self.publish(draft)
        card = self.app.get_learning_entry(self.user.id)["cards"][0]
        self.app.complete_card(self.user.id, "s", card.id)
        self.app.submit_rating(self.user.id, "s", card.id, Rating.REMEMBERED, "same-key")
        with self.assertRaises(ConflictError):
            self.app.submit_rating(self.user.id, "s", card.id, Rating.FORGOT, "same-key")

    def test_invalid_review_does_not_mutate_review_metadata(self):
        draft = self.make_draft()
        with self.assertRaises(ValidationError):
            self.app.content.approve(self.reviewer.id, draft.id, "不应通过", "req")
        self.assertIsNone(draft.reviewed_by)
        self.assertIsNone(draft.review_reason)

    def test_client_timestamp_is_only_allowed_with_small_clock_skew(self):
        draft = self.make_draft()
        self.publish(draft)
        card = self.app.get_learning_entry(self.user.id)["cards"][0]
        self.app.complete_card(self.user.id, "s", card.id)
        with self.assertRaises(ValidationError):
            self.app.submit_rating(
                self.user.id,
                "s",
                card.id,
                Rating.REMEMBERED,
                "future-rating",
                occurred_at=self.clock.value + timedelta(days=1),
            )

    def test_workflow_roles_and_audit_chain(self):
        draft = self.make_draft()
        with self.assertRaises(AuthorizationError):
            self.app.content.approve(self.editor.id, draft.id, "自审", "req")
        self.app.content.submit_for_review(self.editor.id, draft.id, "submit")
        with self.assertRaises(ValidationError):
            self.app.content.publish(self.publisher.id, draft.id, "publish-too-early")
        approved = self.app.content.approve(
            self.reviewer.id, draft.id, "内容合规", "approve"
        )
        self.assertEqual(approved.status, ContentStatus.APPROVED)
        published = self.app.content.publish(self.publisher.id, draft.id, "publish")
        self.assertEqual(published.status, ContentStatus.PUBLISHED)
        self.assertEqual(len(self.app.audits.for_object(draft.id)), 3)
        with self.assertRaises(AuthorizationError):
            self.app.content.unpublish(self.reviewer.id, draft.id, "wrong role", "x")

    def test_revision_does_not_overwrite_published_version(self):
        draft = self.make_draft()
        published = self.publish(draft)
        revision = self.app.content.create_card_revision(self.editor.id, published.card_id)
        self.assertEqual(revision.card_id, published.card_id)
        self.assertEqual(revision.version, 2)
        self.assertEqual(revision.status, ContentStatus.DRAFT)
        self.assertEqual(self.app.content.list_published_cards()[0].id, published.id)

    def test_ai_only_creates_a_draft(self):
        generated = self.app.content.generate_card_draft(
            self.editor.id,
            self.point.id,
            "项目和运营的区别",
            "授权资料",
            "第 1 页",
        )
        self.assertTrue(generated.ai_generated)
        self.assertEqual(generated.status, ContentStatus.DRAFT)
        self.assertEqual(self.app.content.list_published_cards(), [])

    def test_feedback_is_deduplicated_and_can_be_resolved(self):
        draft = self.make_draft()
        self.publish(draft)
        card = self.app.get_learning_entry(self.user.id)["cards"][0]
        first = self.app.submit_content_feedback(
            self.user.id, card.id, FeedbackType.ERROR, "术语需要核对"
        )
        duplicate = self.app.submit_content_feedback(
            self.user.id, card.id, FeedbackType.ERROR, "重复提交"
        )
        self.assertEqual(first.id, duplicate.id)
        resolved = self.app.feedback.resolve(
            self.reviewer.id, first.id, "已创建内容修订任务"
        )
        self.assertEqual(resolved.status.value, "RESOLVED")

    def test_subscription_denial_does_not_block_review_and_reminder_is_idempotent(self):
        draft = self.make_draft()
        self.publish(draft)
        card = self.app.get_learning_entry(self.user.id)["cards"][0]
        self.app.complete_card(self.user.id, "s", card.id)
        self.app.submit_rating(self.user.id, "s", card.id, Rating.FORGOT, "r1")
        self.clock.advance(minutes=11)
        task = self.app.create_daily_reminder(self.user.id, self.clock.value)
        self.assertEqual(task.status, "SKIPPED_UNAUTHORIZED")
        self.assertEqual(len(self.app.wechat.sent), 0)
        self.assertEqual(
            self.app.get_learning_entry(self.user.id)["mode"],
            "REVIEW",
        )
        self.app.request_subscription(self.user.id, True)
        self.clock.advance(days=1)
        sent = self.app.create_daily_reminder(self.user.id, self.clock.value)
        self.assertEqual(sent.status, "SENT")
        self.assertEqual(len(self.app.wechat.sent), 1)
        self.assertEqual(
            sent.id,
            self.app.create_daily_reminder(self.user.id, self.clock.value).id,
        )

    def test_failed_reminder_can_retry_on_the_same_day(self):
        self.app.request_subscription(self.user.id, True)
        self.app.wechat.fail_next = True
        failed = self.app.create_daily_reminder(self.user.id, self.clock.value)
        self.assertEqual(failed.status, "FAILED")
        retried = self.app.create_daily_reminder(self.user.id, self.clock.value)
        self.assertEqual(retried.status, "SENT")
        self.assertEqual(len(self.app.wechat.sent), 1)

    def test_key_events_are_recorded_without_being_required_by_domain(self):
        draft = self.make_draft()
        self.publish(draft)
        card = self.app.get_learning_entry(self.user.id)["cards"][0]
        self.app.complete_card(self.user.id, "s", card.id)
        self.app.submit_rating(self.user.id, "s", card.id, Rating.VAGUE, "r1")
        names = {event.name for event in self.app.analytics.list_events()}
        self.assertIn("login_succeeded", names)
        self.assertIn("content_published", names)
        self.assertIn("card_completed", names)
        self.assertIn("rating_submitted", names)
        self.assertIn("review_plan_updated", names)


if __name__ == "__main__":
    unittest.main()
