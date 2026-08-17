import json
import hashlib
import hmac
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import main
from app.ai_client import AISettings, OpenAICompatibleAIClient
from app.jobs import SummaryJobService
from app.pdf_parser import PDFExtractionError, extract_pdf_text


class FakeAIClient:
    configured = True
    settings = SimpleNamespace(
        model="fake-model",
        base_url="http://fake-ai.local/v1",
    )

    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def summarize(self, title, text, source_type):
        if self.should_fail:
            raise RuntimeError("fake provider unavailable")
        return {
            "summary": f"{title} 的测试总结",
            "key_points": [{"title": "重点", "detail": text[:20]}],
            "cards": [
                {
                    "title": "测试知识点",
                    "conclusion": "这是一个待审核的测试卡片。",
                    "explanation": "用于验证后端输出结构。",
                    "example": "使用 Fake AI 完成测试。",
                    "recall_prompt": "这张卡片的状态是什么？",
                    "reference_answer": "USER_DRAFT。",
                    "source_locator": "第 1 页",
                    "status": "USER_DRAFT",
                }
            ],
            "quality_warnings": [],
            "model_version": "fake-model",
            "source_type": source_type,
            "input_chars": len(text),
            "input_truncated": False,
        }


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    def __init__(self, _stream):
        self.pages = [FakePage("第一页内容"), FakePage("第二页内容")]


class BackendTestCase(unittest.TestCase):
    def setUp(self):
        self.previous_job_service = main.job_service
        main.job_service = SummaryJobService(FakeAIClient())
        self.client = TestClient(main.app)
        self.client.headers.update({"X-User-ID": "test-user"})

    def tearDown(self):
        main.job_service = self.previous_job_service

    def test_health_reports_ai_configuration(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["ai_configured"])

    def test_text_summary_returns_user_draft_result(self):
        response = self.client.post(
            "/api/v1/summaries/text",
            json={"title": "项目管理", "text": "项目是临时性的工作。"},
        )

        self.assertEqual(response.status_code, 202)
        task = self.client.get(
            f"/api/v1/summaries/{response.json()['task_id']}"
        ).json()
        self.assertEqual(task["status"], "DRAFT_READY")
        self.assertEqual(task["result"]["cards"][0]["status"], "USER_DRAFT")

    def test_summary_task_is_scoped_to_owner(self):
        response = self.client.post(
            "/api/v1/summaries/text",
            json={"title": "私有资料", "text": "只属于测试用户。"},
        )
        task_id = response.json()["task_id"]
        other = self.client.get(
            f"/api/v1/summaries/{task_id}",
            headers={"X-User-ID": "other-user"},
        )
        self.assertEqual(other.status_code, 404)

    def test_summary_requires_user_identity(self):
        response = self.client.post(
            "/api/v1/summaries/text",
            headers={"X-User-ID": ""},
            json={"text": "没有身份的请求"},
        )
        self.assertEqual(response.status_code, 401)

    def test_signed_user_identity_is_required_when_configured(self):
        user_id = "signed-user"
        signature = hmac.new(
            b"test-secret", user_id.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        with patch.dict(
            os.environ,
            {
                "USER_ID_SIGNING_SECRET": "test-secret",
                "ALLOW_INSECURE_DEV_IDENTITY": "false",
            },
        ):
            response = self.client.post(
                "/api/v1/summaries/text",
                headers={
                    "X-User-ID": user_id,
                    "X-User-Signature": signature,
                },
                json={"text": "带签名的用户资料"},
            )
        self.assertEqual(response.status_code, 202)

    def test_pdf_upload_is_rejected_before_unbounded_read(self):
        with patch("app.main.max_pdf_bytes", return_value=1024):
            response = self.client.post(
                "/api/v1/summaries/pdf",
                data={"title": "过大 PDF"},
                files={"file": ("study.pdf", b"x" * 1025, "application/pdf")},
            )
        self.assertEqual(response.status_code, 413)

    def test_pdf_summary_extracts_text_before_generation(self):
        with patch("app.main.extract_pdf_text", return_value="[第 1 页]\n项目资料"):
            response = self.client.post(
                "/api/v1/summaries/pdf",
                data={"title": "PDF 测试"},
                files={"file": ("study.pdf", b"fake-pdf", "application/pdf")},
            )

        self.assertEqual(response.status_code, 202)
        task = self.client.get(
            f"/api/v1/summaries/{response.json()['task_id']}"
        ).json()
        self.assertEqual(task["source_type"], "pdf")
        self.assertEqual(task["source_name"], "study.pdf")
        self.assertEqual(task["status"], "DRAFT_READY")

    def test_provider_failure_is_visible_in_task(self):
        main.job_service = SummaryJobService(FakeAIClient(should_fail=True))

        response = self.client.post(
            "/api/v1/summaries/text",
            json={"text": "会失败的测试资料"},
        )

        task = self.client.get(
            f"/api/v1/summaries/{response.json()['task_id']}"
        ).json()
        self.assertEqual(task["status"], "FAILED")
        self.assertEqual(task["error"], "fake provider unavailable")

    def test_pdf_parser_preserves_page_markers(self):
        with patch("app.pdf_parser.PdfReader", FakeReader):
            extracted = extract_pdf_text(b"valid-for-fake-reader")

        self.assertIn("[第 1 页]", extracted)
        self.assertIn("第一页内容", extracted)
        self.assertIn("[第 2 页]", extracted)

    def test_pdf_parser_rejects_scanned_pdf_without_text(self):
        class EmptyReader:
            def __init__(self, _stream):
                self.pages = [FakePage("")]

        with patch("app.pdf_parser.PdfReader", EmptyReader):
            with self.assertRaises(PDFExtractionError):
                extract_pdf_text(b"valid-for-fake-reader")

    def test_openai_compatible_client_normalizes_json_response(self):
        class Response:
            def read(self):
                return json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "summary": "ok",
                                            "key_points": [],
                                            "cards": [],
                                            "quality_warnings": [],
                                        }
                                    )
                                }
                            }
                        ]
                    }
                ).encode("utf-8")

            def close(self):
                return None

        def opener(_request, timeout):
            self.assertEqual(timeout, 3.0)
            return Response()

        client = OpenAICompatibleAIClient(
            AISettings(
                base_url="http://fake-ai.local/v1",
                api_key="test-key",
                model="fake-model",
                timeout_seconds=3.0,
                max_input_chars=1000,
            ),
            opener=opener,
        )
        result = client.summarize("标题", "正文", "text")

        self.assertEqual(result["summary"], "ok")
        self.assertEqual(result["model_version"], "fake-model")


if __name__ == "__main__":
    unittest.main()
