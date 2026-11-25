import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select
from starlette.requests import Request

from app.admin.router import router as admin_router
from app.audit.service import _has_repeated_failures
from app.auth.jwt import create_access_token
from app.auth.router import get_client_ip, router as auth_router
from app.models.audit_log import AuditLog
from app.models.user import User
from database import get_session


class AdminSecurityDashboardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.app = FastAPI()
        cls.app.include_router(admin_router)
        cls.app.include_router(auth_router)

        def override_get_session():
            with Session(cls.engine) as session:
                yield session

        cls.app.dependency_overrides[get_session] = override_get_session
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

        self.admin = User(
            id=uuid4(),
            email="admin@test.com",
            name="Test Admin",
            password_hash="test-hash",
            role="ADMIN",
            is_active=True,
        )
        self.student = User(
            id=uuid4(),
            email="student@test.com",
            name="Test Student",
            password_hash="test-hash",
            role="STUDENT",
            is_active=True,
        )
        with Session(self.engine) as session:
            session.add(self.admin)
            session.add(self.student)
            session.commit()
            session.refresh(self.admin)
            session.refresh(self.student)

        self.now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    def token_for(self, user: User) -> str:
        return create_access_token(
            user.id,
            user.role,
            user.token_version,
        )

    def seed_event(
        self,
        action: str,
        created_at: datetime,
        *,
        email: str | None = None,
        ip_address: str = "198.51.100.10",
        reason: str = "test reason",
    ) -> None:
        with Session(self.engine) as session:
            session.add(
                AuditLog(
                    action=action,
                    email=email,
                    ip_address=ip_address,
                    details=json.dumps({"reason": reason}),
                    created_at=created_at,
                )
            )
            session.commit()

    def get_security_dashboard(self, **params):
        return self.client.get(
            "/api/admin/security/failed-logins",
            headers={
                "Authorization": f"Bearer {self.token_for(self.admin)}",
            },
            params=params,
        )

    def test_dashboard_groups_failures_and_separates_rate_limits(self):
        first_attempt = self.now - timedelta(minutes=15)
        for index in range(5):
            self.seed_event(
                "LOGIN_FAILED",
                first_attempt + timedelta(minutes=3 * index, seconds=45 * index),
                email="  Person@Example.com ",
            )

        for index in range(15):
            self.seed_event(
                "LOGIN_FAILED",
                self.now - timedelta(minutes=10) + timedelta(seconds=index),
                email=f"other{index}@example.com",
            )

        self.seed_event(
            "LOGIN_RATE_LIMITED",
            self.now - timedelta(minutes=1),
            email="person@example.com",
            reason="Login rate limit exceeded",
        )
        self.seed_event(
            "LOGIN_SUCCESS",
            self.now - timedelta(minutes=2),
            email="person@example.com",
        )
        self.seed_event(
            "LOGIN_FAILED",
            self.now - timedelta(days=1),
            email="outside@example.com",
        )

        response = self.get_security_dashboard(
            start_date="2026-01-01T00:00:00Z",
            end_date="2026-01-01T23:59:59Z",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_failed"], 20)
        self.assertEqual(data["total_rate_limited"], 1)
        self.assertEqual(data["total"], 21)

        ip_summary = next(
            item for item in data["by_ip"]
            if item["ip_address"] == "198.51.100.10"
        )
        self.assertEqual(ip_summary["failed_count"], 20)
        self.assertEqual(ip_summary["rate_limited_count"], 1)
        self.assertTrue(ip_summary["repeated"])

        email_summary = next(
            item for item in data["by_email"]
            if item["email"] == "person@example.com"
        )
        self.assertEqual(email_summary["failed_count"], 5)
        self.assertEqual(email_summary["rate_limited_count"], 1)
        self.assertTrue(email_summary["repeated"])

        rate_limited_event = next(
            event for event in data["events"]
            if event["action"] == "LOGIN_RATE_LIMITED"
        )
        self.assertEqual(
            rate_limited_event["reason"],
            "Login rate limit exceeded",
        )

    def test_dashboard_default_range_is_last_seven_days(self):
        response = self.get_security_dashboard()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        start = datetime.fromisoformat(data["start_date"])
        end = datetime.fromisoformat(data["end_date"])
        self.assertEqual(end - start, timedelta(days=7))

    def test_dashboard_rejects_reversed_and_overlong_ranges(self):
        reversed_response = self.get_security_dashboard(
            start_date="2026-01-02T00:00:00Z",
            end_date="2026-01-01T00:00:00Z",
        )
        self.assertEqual(reversed_response.status_code, 400)
        self.assertIn(
            "start_date cannot be later",
            reversed_response.json()["detail"],
        )

        valid_response = self.get_security_dashboard(
            start_date="2026-01-01T00:00:00Z",
            end_date="2026-03-31T23:59:59Z",
        )
        self.assertEqual(valid_response.status_code, 200)

        overlong_response = self.get_security_dashboard(
            start_date="2026-01-01T00:00:00Z",
            end_date="2026-04-01T00:00:00Z",
        )
        self.assertEqual(overlong_response.status_code, 400)
        self.assertIn(
            "cannot exceed 90 days",
            overlong_response.json()["detail"],
        )

    def test_dashboard_requires_administrator_authorization(self):
        anonymous_response = self.client.get(
            "/api/admin/security/failed-logins"
        )
        self.assertEqual(anonymous_response.status_code, 401)

        student_response = self.client.get(
            "/api/admin/security/failed-logins",
            headers={
                "Authorization": f"Bearer {self.token_for(self.student)}",
            },
        )
        self.assertEqual(student_response.status_code, 403)

    def test_repeated_failure_thresholds_use_inclusive_15_minute_windows(self):
        start = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        email_at_threshold = [
            start + timedelta(minutes=3 * index, seconds=45 * index)
            for index in range(5)
        ]
        email_over_window = [
            start + timedelta(minutes=3 * index)
            for index in range(4)
        ] + [start + timedelta(minutes=15, microseconds=1)]

        ip_at_threshold = [
            start + timedelta(seconds=45 * index)
            for index in range(20)
        ]
        ip_over_window = [
            start + timedelta(seconds=45 * index)
            for index in range(19)
        ] + [start + timedelta(minutes=15, microseconds=1)]

        self.assertTrue(
            _has_repeated_failures(email_at_threshold, 5, start)
        )
        self.assertFalse(
            _has_repeated_failures(email_over_window, 5, start)
        )
        self.assertFalse(
            _has_repeated_failures(email_at_threshold[:4], 5, start)
        )
        self.assertTrue(
            _has_repeated_failures(ip_at_threshold, 20, start)
        )
        self.assertFalse(
            _has_repeated_failures(ip_over_window, 20, start)
        )
        self.assertFalse(
            _has_repeated_failures(ip_at_threshold[:19], 20, start)
        )

    def test_login_audit_uses_authentication_resolved_proxy_ip(self):
        with patch.dict(os.environ, {"VERCEL": "1"}):
            response = self.client.post(
                "/api/auth/login",
                json={
                    "email": "  Mixed@Example.com ",
                    "password": "WrongPassword123",
                },
                headers={
                    "x-forwarded-for": "203.0.113.42, 10.0.0.1",
                },
            )

        self.assertEqual(response.status_code, 401)
        with Session(self.engine) as session:
            event = session.exec(
                select(AuditLog).where(AuditLog.action == "LOGIN_FAILED")
            ).one()

        self.assertEqual(event.ip_address, "203.0.113.42")
        self.assertEqual(event.email, "mixed@example.com")

    def test_client_ip_resolution_does_not_trust_forwarded_header_locally(self):
        request = Request({
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "query_string": b"",
            "headers": [
                (b"x-forwarded-for", b"203.0.113.42, 10.0.0.1"),
            ],
            "client": ("192.0.2.10", 1234),
            "server": ("testserver", 80),
        })

        with patch.dict(os.environ, {"VERCEL": "0"}):
            self.assertEqual(get_client_ip(request), "192.0.2.10")

        with patch.dict(os.environ, {"VERCEL": "1"}):
            self.assertEqual(get_client_ip(request), "203.0.113.42")

            invalid_request = Request({
                **request.scope,
                "headers": [
                    (b"x-forwarded-for", b"not-an-ip"),
                ],
            })
            self.assertEqual(get_client_ip(invalid_request), "unknown")


if __name__ == "__main__":
    unittest.main()
