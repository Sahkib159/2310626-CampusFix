import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.admin.router import router as admin_router
from app.auth.dependencies import get_current_admin
from app.models.audit_log import AuditLog
from app.models.refresh_session import RefreshSession
from app.models.user import User
from app.auth.permissions import ADMIN, require_user_role
from database import get_session


class AdminBulkUserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        cls.app = FastAPI()
        cls.app.include_router(admin_router)
        cls.current_admin_id = None

        def override_get_current_admin():
            if cls.current_admin_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token.",
                )

            with Session(cls.engine) as session:
                user = session.get(User, cls.current_admin_id)
                if user is None:
                    raise RuntimeError("Test admin not found.")
                session.expunge(user)
                return require_user_role(user, ADMIN)

        def override_get_session():
            with Session(cls.engine) as session:
                yield session

        cls.app.dependency_overrides[get_current_admin] = (
            override_get_current_admin
        )
        cls.app.dependency_overrides[get_session] = (
            override_get_session
        )

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

        self.admin_id = uuid4()
        self.other_admin_id = uuid4()
        self.student_a_id = uuid4()
        self.student_b_id = uuid4()
        self.staff_id = uuid4()
        self.banned_id = uuid4()

        users = [
            User(
                id=self.admin_id,
                email="admin@test.com",
                name="Admin",
                password_hash="test-hash",
                role="ADMIN",
            ),
            User(
                id=self.other_admin_id,
                email="other-admin@test.com",
                name="Other Admin",
                password_hash="test-hash",
                role="ADMIN",
            ),
            User(
                id=self.student_a_id,
                email="student-a@test.com",
                name="Student A",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.student_b_id,
                email="student-b@test.com",
                name="Student B",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.staff_id,
                email="staff@test.com",
                name="Staff",
                password_hash="test-hash",
                role="STAFF",
            ),
            User(
                id=self.banned_id,
                email="banned@test.com",
                name="Banned Student",
                password_hash="test-hash",
                role="STUDENT",
                is_banned=True,
                ban_reason="Previously banned",
                banned_at=datetime.now(timezone.utc),
                banned_by=self.admin_id,
            ),
        ]

        with Session(self.engine) as session:
            session.add_all(users)
            session.commit()

        type(self).current_admin_id = self.admin_id

    def login_as(self, user_id):
        type(self).current_admin_id = user_id

    def get_user(self, user_id):
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            session.expunge(user)
            return user

    def get_audit_logs(self, action=None):
        with Session(self.engine) as session:
            statement = select(AuditLog).order_by(AuditLog.created_at)
            if action is not None:
                statement = statement.where(AuditLog.action == action)
            return list(session.exec(statement).all())

    def test_bulk_operations_reject_missing_admin(self):
        type(self).current_admin_id = None

        for method, url, payload in (
            (
                self.client.post,
                "/api/admin/users/bulk-ban",
                {
                    "user_ids": [str(self.student_a_id)],
                    "reason": "Policy violation",
                },
            ),
            (
                self.client.post,
                "/api/admin/users/bulk-unban",
                {"user_ids": [str(self.banned_id)]},
            ),
        ):
            with self.subTest(url=url):
                response = method(url, json=payload)
                self.assertEqual(response.status_code, 401)

    def test_bulk_ban_rejects_non_admin(self):
        self.login_as(self.student_a_id)

        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [str(self.student_b_id)],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_bulk_unban_rejects_non_admin(self):
        self.login_as(self.student_a_id)

        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={"user_ids": [str(self.banned_id)]},
        )

        self.assertEqual(response.status_code, 403)

    def test_bulk_ban_success(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [
                    str(self.student_a_id),
                    str(self.student_b_id),
                ],
                "reason": "Repeated policy violations",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(body["succeeded"], 2)
        self.assertEqual(body["failed"], 0)
        self.assertTrue(all(item["success"] for item in body["results"]))

        for user_id in (self.student_a_id, self.student_b_id):
            user = self.get_user(user_id)
            self.assertTrue(user.is_banned)
            self.assertEqual(
                user.ban_reason,
                "Repeated policy violations",
            )
            self.assertIsNotNone(user.banned_at)
            self.assertEqual(user.banned_by, self.admin_id)

    def test_bulk_unban_success(self):
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={"user_ids": [str(self.banned_id)]},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["succeeded"], 1)
        self.assertEqual(body["failed"], 0)

        user = self.get_user(self.banned_id)
        self.assertFalse(user.is_banned)
        self.assertIsNone(user.ban_reason)
        self.assertIsNone(user.banned_at)
        self.assertIsNone(user.banned_by)

    def test_bulk_ban_mixed_success_failure_isolated(self):
        missing_id = uuid4()
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [
                    str(self.student_a_id),
                    str(missing_id),
                    str(self.banned_id),
                    str(self.other_admin_id),
                    str(self.admin_id),
                ],
                "reason": "Bulk policy violation",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 5)
        self.assertEqual(body["succeeded"], 1)
        self.assertEqual(body["failed"], 4)

        results = {
            item["user_id"]: item
            for item in body["results"]
        }
        self.assertTrue(results[str(self.student_a_id)]["success"])
        self.assertFalse(results[str(missing_id)]["success"])
        self.assertEqual(
            results[str(missing_id)]["message"],
            "User not found.",
        )
        self.assertFalse(results[str(self.banned_id)]["success"])
        self.assertFalse(results[str(self.other_admin_id)]["success"])
        self.assertFalse(results[str(self.admin_id)]["success"])

        self.assertTrue(self.get_user(self.student_a_id).is_banned)
        self.assertTrue(self.get_user(self.banned_id).is_banned)
        self.assertFalse(self.get_user(self.other_admin_id).is_banned)
        self.assertFalse(self.get_user(self.admin_id).is_banned)

    def test_bulk_unban_mixed_success_failure_isolated(self):
        missing_id = uuid4()
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={
                "user_ids": [
                    str(self.banned_id),
                    str(missing_id),
                    str(self.student_a_id),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 3)
        self.assertEqual(body["succeeded"], 1)
        self.assertEqual(body["failed"], 2)

        results = {
            item["user_id"]: item
            for item in body["results"]
        }
        self.assertTrue(results[str(self.banned_id)]["success"])
        self.assertFalse(results[str(missing_id)]["success"])
        self.assertFalse(results[str(self.student_a_id)]["success"])

        self.assertFalse(self.get_user(self.banned_id).is_banned)
        self.assertFalse(self.get_user(self.student_a_id).is_banned)

    def test_bulk_ban_missing_user(self):
        missing_id = uuid4()
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [str(missing_id)],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "User not found.")

    def test_bulk_ban_already_banned_user(self):
        existing_user = self.get_user(self.banned_id)
        existing_banned_at = existing_user.banned_at

        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [str(self.banned_id)],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertFalse(result["success"])
        self.assertEqual(
            result["message"],
            "This user is already banned.",
        )

        unchanged_user = self.get_user(self.banned_id)
        self.assertTrue(unchanged_user.is_banned)
        self.assertEqual(
            unchanged_user.ban_reason,
            "Previously banned",
        )
        self.assertEqual(
            unchanged_user.banned_at,
            existing_banned_at,
        )
        self.assertEqual(
            unchanged_user.banned_by,
            self.admin_id,
        )

    def test_bulk_unban_missing_and_not_banned_users(self):
        missing_id = uuid4()
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={
                "user_ids": [
                    str(missing_id),
                    str(self.student_a_id),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        results = {
            item["user_id"]: item
            for item in response.json()["results"]
        }
        self.assertEqual(
            results[str(missing_id)]["message"],
            "User not found.",
        )
        self.assertEqual(
            results[str(self.student_a_id)]["message"],
            "This user is not currently banned.",
        )

        unchanged_user = self.get_user(self.student_a_id)
        self.assertFalse(unchanged_user.is_banned)
        self.assertIsNone(unchanged_user.ban_reason)
        self.assertIsNone(unchanged_user.banned_at)
        self.assertIsNone(unchanged_user.banned_by)

    def test_bulk_ban_rejects_self_and_other_admin(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [
                    str(self.admin_id),
                    str(self.other_admin_id),
                ],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["succeeded"], 0)
        self.assertEqual(body["failed"], 2)

        results = {
            item["user_id"]: item["message"]
            for item in body["results"]
        }
        self.assertEqual(
            results[str(self.admin_id)],
            "You cannot ban your own account.",
        )
        self.assertEqual(
            results[str(self.other_admin_id)],
            "Administrators cannot be banned through this endpoint.",
        )
        self.assertFalse(self.get_user(self.admin_id).is_banned)
        self.assertFalse(self.get_user(self.other_admin_id).is_banned)

    def test_bulk_ban_revokes_active_refresh_sessions(self):
        active_session = RefreshSession(
            user_id=self.student_a_id,
            family_id=uuid4(),
            token_hash="active-token-hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        unrelated_active_session = RefreshSession(
            user_id=self.student_b_id,
            family_id=uuid4(),
            token_hash="unrelated-active-token-hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        already_revoked = RefreshSession(
            user_id=self.student_a_id,
            family_id=uuid4(),
            token_hash="revoked-token-hash",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        with Session(self.engine) as session:
            session.add_all([
                active_session,
                unrelated_active_session,
                already_revoked,
            ])
            session.commit()
            session.refresh(already_revoked)
            previous_revoked_at = already_revoked.revoked_at

        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [str(self.student_a_id)],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["results"][0]["success"])

        with Session(self.engine) as session:
            sessions = list(
                session.exec(select(RefreshSession)).all()
            )

        by_hash = {
            item.token_hash: item
            for item in sessions
        }
        self.assertIsNotNone(
            by_hash["active-token-hash"].revoked_at
        )
        self.assertEqual(
            by_hash["revoked-token-hash"].revoked_at,
            previous_revoked_at,
        )
        self.assertIsNone(
            by_hash["unrelated-active-token-hash"].revoked_at
        )

    def test_bulk_ban_audit_event_only_for_successful_items(self):
        missing_id = uuid4()
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [
                    str(self.student_a_id),
                    str(missing_id),
                    str(self.banned_id),
                ],
                "reason": "Security incident",
            },
        )

        self.assertEqual(response.status_code, 200)
        logs = self.get_audit_logs("USER_BANNED")
        self.assertEqual(len(logs), 1)

        log = logs[0]
        self.assertEqual(log.actor_id, self.admin_id)
        self.assertEqual(log.target_user_id, self.student_a_id)
        self.assertEqual(log.email, "student-a@test.com")
        self.assertIn("Security incident", log.details)

    def test_bulk_unban_audit_event_only_for_successful_items(self):
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={
                "user_ids": [
                    str(self.banned_id),
                    str(self.student_a_id),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        logs = self.get_audit_logs("USER_UNBANNED")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].actor_id, self.admin_id)
        self.assertEqual(logs[0].target_user_id, self.banned_id)
        self.assertEqual(logs[0].email, "banned@test.com")

    def test_bulk_ban_duplicate_ids_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [
                    str(self.student_a_id),
                    str(self.student_a_id),
                ],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_bulk_unban_duplicate_ids_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={
                "user_ids": [
                    str(self.banned_id),
                    str(self.banned_id),
                ],
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_bulk_ban_empty_list_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_bulk_unban_empty_list_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={"user_ids": []},
        )

        self.assertEqual(response.status_code, 422)

    def test_bulk_ban_more_than_100_ids_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [str(uuid4()) for _ in range(101)],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_bulk_unban_more_than_100_ids_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-unban",
            json={"user_ids": [str(uuid4()) for _ in range(101)]},
        )

        self.assertEqual(response.status_code, 422)

    def test_bulk_ban_invalid_reasons_rejected(self):
        for reason in ("", "xy", "x" * 501):
            with self.subTest(reason_length=len(reason)):
                response = self.client.post(
                    "/api/admin/users/bulk-ban",
                    json={
                        "user_ids": [str(self.student_a_id)],
                        "reason": reason,
                    },
                )
                self.assertEqual(response.status_code, 422)

    def test_bulk_ban_whitespace_reason_handled_per_user(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": [str(self.student_a_id)],
                "reason": "   ",
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"][0]
        self.assertFalse(result["success"])
        self.assertEqual(
            result["message"],
            "Ban reason must contain at least 3 characters.",
        )
        self.assertFalse(self.get_user(self.student_a_id).is_banned)

    def test_invalid_uuid_rejected(self):
        response = self.client.post(
            "/api/admin/users/bulk-ban",
            json={
                "user_ids": ["not-a-uuid"],
                "reason": "Policy violation",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_individual_ban_still_works(self):
        response = self.client.post(
            f"/api/admin/users/{self.student_a_id}/ban",
            json={"reason": "Individual ban"},
        )

        self.assertEqual(response.status_code, 200)
        user = self.get_user(self.student_a_id)
        self.assertTrue(user.is_banned)
        self.assertEqual(user.ban_reason, "Individual ban")
        self.assertIsNotNone(user.banned_at)
        self.assertEqual(user.banned_by, self.admin_id)

        logs = self.get_audit_logs("USER_BANNED")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].target_user_id, self.student_a_id)

    def test_admin_can_revoke_one_session_family(self):
        now = datetime.now(timezone.utc)
        family_id = uuid4()
        other_family_id = uuid4()
        another_users_family_id = uuid4()
        historical_revocation = now - timedelta(days=1)

        refresh_sessions = [
            RefreshSession(
                user_id=self.student_a_id,
                family_id=family_id,
                token_hash="target-family-historical-token",
                expires_at=now + timedelta(days=1),
                revoked_at=historical_revocation,
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=family_id,
                token_hash="target-family-current-token",
                expires_at=now + timedelta(days=10),
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=other_family_id,
                token_hash="target-other-family-token",
                expires_at=now + timedelta(days=10),
            ),
            RefreshSession(
                user_id=self.student_b_id,
                family_id=another_users_family_id,
                token_hash="other-user-family-token",
                expires_at=now + timedelta(days=10),
            ),
        ]

        with Session(self.engine) as session:
            session.add_all(refresh_sessions)
            session.commit()

        token_version_before = self.get_user(
            self.student_a_id,
        ).token_version

        response = self.client.delete(
            f"/api/admin/users/{self.student_a_id}/sessions/{family_id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Session family revoked successfully.",
        )

        with Session(self.engine) as session:
            stored_sessions = {
                item.token_hash: item
                for item in session.exec(
                    select(RefreshSession)
                ).all()
            }

        self.assertEqual(
            stored_sessions[
                "target-family-historical-token"
            ].revoked_at,
            historical_revocation,
        )
        self.assertIsNotNone(
            stored_sessions[
                "target-family-current-token"
            ].revoked_at
        )
        self.assertIsNone(
            stored_sessions[
                "target-other-family-token"
            ].revoked_at
        )
        self.assertIsNone(
            stored_sessions[
                "other-user-family-token"
            ].revoked_at
        )
        self.assertEqual(
            self.get_user(self.student_a_id).token_version,
            token_version_before,
        )

        logs = self.get_audit_logs("USER_SESSION_REVOKED")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].actor_id, self.admin_id)
        self.assertEqual(logs[0].target_user_id, self.student_a_id)
        self.assertEqual(
            json.loads(logs[0].details),
            {"family_id": str(family_id), "changed": True},
        )

    def test_session_family_revocation_requires_admin(self):
        family_id = uuid4()

        for user_id, expected_status in (
            (None, 401),
            (self.student_a_id, 403),
            (self.staff_id, 403),
        ):
            with self.subTest(user_id=user_id):
                type(self).current_admin_id = user_id

                response = self.client.delete(
                    f"/api/admin/users/{self.student_b_id}"
                    f"/sessions/{family_id}",
                )

                self.assertEqual(
                    response.status_code,
                    expected_status,
                )

    def test_session_family_id_collision_is_scoped_to_target_user(self):
        family_id = uuid4()
        now = datetime.now(timezone.utc)
        target_session = RefreshSession(
            user_id=self.student_a_id,
            family_id=family_id,
            token_hash="collision-target-user-token",
            expires_at=now + timedelta(days=1),
        )
        other_user_session = RefreshSession(
            user_id=self.student_b_id,
            family_id=family_id,
            token_hash="collision-other-user-token",
            expires_at=now + timedelta(days=1),
        )

        with Session(self.engine) as session:
            session.add_all([target_session, other_user_session])
            session.commit()

        response = self.client.delete(
            f"/api/admin/users/{self.student_a_id}/sessions/{family_id}",
        )

        self.assertEqual(response.status_code, 200)
        with Session(self.engine) as session:
            stored_sessions = {
                item.token_hash: item
                for item in session.exec(
                    select(RefreshSession)
                ).all()
            }

        self.assertIsNotNone(
            stored_sessions["collision-target-user-token"].revoked_at
        )
        self.assertIsNone(
            stored_sessions["collision-other-user-token"].revoked_at
        )

    def test_session_family_belonging_to_another_user_is_not_found(self):
        family_id = uuid4()
        refresh_session = RefreshSession(
            user_id=self.student_b_id,
            family_id=family_id,
            token_hash="foreign-session-family-token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        with Session(self.engine) as session:
            session.add(refresh_session)
            session.commit()

        response = self.client.delete(
            f"/api/admin/users/{self.student_a_id}/sessions/{family_id}",
        )

        self.assertEqual(response.status_code, 404)
        with Session(self.engine) as session:
            stored = session.exec(
                select(RefreshSession).where(
                    RefreshSession.token_hash
                    == "foreign-session-family-token"
                )
            ).one()
        self.assertIsNone(stored.revoked_at)
        self.assertEqual(
            self.get_audit_logs("USER_SESSION_REVOKED"),
            [],
        )

    def test_session_family_revocation_handles_missing_records(self):
        missing_user_id = uuid4()
        missing_family_id = uuid4()

        for user_id, family_id in (
            (missing_user_id, missing_family_id),
            (self.student_a_id, missing_family_id),
        ):
            with self.subTest(user_id=user_id, family_id=family_id):
                response = self.client.delete(
                    f"/api/admin/users/{user_id}/sessions/{family_id}",
                )
                self.assertEqual(response.status_code, 404)

        self.assertEqual(
            self.get_audit_logs("USER_SESSION_REVOKED"),
            [],
        )

    def test_already_revoked_session_family_is_idempotent(self):
        family_id = uuid4()
        previous_revocation = datetime.now(timezone.utc) - timedelta(days=1)
        refresh_session = RefreshSession(
            user_id=self.student_a_id,
            family_id=family_id,
            token_hash="already-revoked-session-family-token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            revoked_at=previous_revocation,
        )

        with Session(self.engine) as session:
            session.add(refresh_session)
            session.commit()

        response = self.client.delete(
            f"/api/admin/users/{self.student_a_id}/sessions/{family_id}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["message"],
            "Session family revoked successfully.",
        )
        with Session(self.engine) as session:
            stored = session.exec(
                select(RefreshSession).where(
                    RefreshSession.token_hash
                    == "already-revoked-session-family-token"
                )
            ).one()
        self.assertEqual(
            stored.revoked_at,
            previous_revocation,
        )

        logs = self.get_audit_logs("USER_SESSION_REVOKED")
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            json.loads(logs[0].details),
            {"family_id": str(family_id), "changed": False},
        )

    def test_session_revocation_rolls_back_when_audit_write_fails(self):
        family_id = uuid4()
        now = datetime.now(timezone.utc)
        refresh_sessions = [
            RefreshSession(
                user_id=self.student_a_id,
                family_id=family_id,
                token_hash="audit-failure-target-token",
                expires_at=now + timedelta(days=1),
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=uuid4(),
                token_hash="audit-failure-other-family-token",
                expires_at=now + timedelta(days=1),
            ),
            RefreshSession(
                user_id=self.student_b_id,
                family_id=family_id,
                token_hash="audit-failure-colliding-user-token",
                expires_at=now + timedelta(days=1),
            ),
        ]

        with Session(self.engine) as session:
            session.add_all(refresh_sessions)
            session.commit()

        def fail_audit_write(session, audit_log):
            session.add(audit_log)
            raise SQLAlchemyError("Simulated audit write failure.")

        with TestClient(
            self.app,
            raise_server_exceptions=False,
        ) as client:
            with patch(
                "app.audit.service.create_audit_log",
                side_effect=fail_audit_write,
            ):
                response = client.delete(
                    f"/api/admin/users/{self.student_a_id}"
                    f"/sessions/{family_id}",
                )

        self.assertEqual(response.status_code, 500)

        with Session(self.engine) as session:
            stored_sessions = {
                item.token_hash: item
                for item in session.exec(
                    select(RefreshSession)
                ).all()
            }

        self.assertIsNone(
            stored_sessions["audit-failure-target-token"].revoked_at
        )
        self.assertIsNone(
            stored_sessions["audit-failure-other-family-token"].revoked_at
        )
        self.assertIsNone(
            stored_sessions["audit-failure-colliding-user-token"].revoked_at
        )
        self.assertEqual(
            self.get_audit_logs("USER_SESSION_REVOKED"),
            [],
        )

    def test_user_detail_groups_refresh_sessions_by_family(self):
        now = datetime.now(timezone.utc)
        active_family_id = uuid4()
        revoked_family_id = uuid4()
        expired_family_id = uuid4()

        refresh_sessions = [
            RefreshSession(
                user_id=self.student_a_id,
                family_id=active_family_id,
                token_hash="active-family-historical-token",
                created_at=now - timedelta(days=3),
                expires_at=now + timedelta(days=1),
                revoked_at=now - timedelta(days=2),
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=active_family_id,
                token_hash="active-family-current-token",
                created_at=now - timedelta(days=1),
                expires_at=now + timedelta(days=10),
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=revoked_family_id,
                token_hash="revoked-family-old-token",
                created_at=now - timedelta(days=5),
                expires_at=now + timedelta(days=2),
                revoked_at=now - timedelta(days=3),
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=revoked_family_id,
                token_hash="revoked-family-current-token",
                created_at=now - timedelta(days=4),
                expires_at=now + timedelta(days=3),
                revoked_at=now - timedelta(days=2),
            ),
            RefreshSession(
                user_id=self.student_a_id,
                family_id=expired_family_id,
                token_hash="expired-family-token",
                created_at=now - timedelta(days=6),
                expires_at=now - timedelta(days=1),
            ),
        ]

        with Session(self.engine) as session:
            session.add_all(refresh_sessions)
            session.commit()

        response = self.client.get(
            f"/api/admin/users/{self.student_a_id}",
        )

        self.assertEqual(response.status_code, 200)
        sessions = response.json()["sessions"]
        self.assertEqual(len(sessions), 3)
        sessions_by_id = {
            item["id"]: item
            for item in sessions
        }

        active = sessions_by_id[str(active_family_id)]
        self.assertTrue(active["is_active"])
        self.assertIsNone(active["revoked_at"])
        self.assertEqual(
            datetime.fromisoformat(active["created_at"]).replace(
                tzinfo=timezone.utc,
            ),
            now - timedelta(days=3),
        )
        self.assertEqual(
            datetime.fromisoformat(active["expires_at"]).replace(
                tzinfo=timezone.utc,
            ),
            now + timedelta(days=10),
        )

        revoked = sessions_by_id[str(revoked_family_id)]
        self.assertFalse(revoked["is_active"])
        self.assertEqual(
            datetime.fromisoformat(revoked["revoked_at"]).replace(
                tzinfo=timezone.utc,
            ),
            now - timedelta(days=2),
        )

        expired = sessions_by_id[str(expired_family_id)]
        self.assertFalse(expired["is_active"])
        self.assertIsNone(expired["revoked_at"])
        self.assertNotIn("token_hash", sessions[0])

    def test_individual_unban_still_works(self):
        response = self.client.post(
            f"/api/admin/users/{self.banned_id}/unban",
        )

        self.assertEqual(response.status_code, 200)
        user = self.get_user(self.banned_id)
        self.assertFalse(user.is_banned)
        self.assertIsNone(user.ban_reason)
        self.assertIsNone(user.banned_at)
        self.assertIsNone(user.banned_by)

        logs = self.get_audit_logs("USER_UNBANNED")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].target_user_id, self.banned_id)

    def test_individual_ban_protects_self_and_other_admin(self):
        protected_targets = (
            (self.admin_id, 400),
            (self.other_admin_id, 403),
        )

        for target_id, expected_status in protected_targets:
            with self.subTest(target_id=target_id):
                response = self.client.post(
                    f"/api/admin/users/{target_id}/ban",
                    json={"reason": "Policy violation"},
                )
                self.assertEqual(
                    response.status_code,
                    expected_status,
                )
                self.assertFalse(
                    self.get_user(target_id).is_banned
                )

    def test_individual_ban_revokes_refresh_sessions(self):
        refresh_session = RefreshSession(
            user_id=self.student_a_id,
            family_id=uuid4(),
            token_hash="individual-active-token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        with Session(self.engine) as session:
            session.add(refresh_session)
            session.commit()

        response = self.client.post(
            f"/api/admin/users/{self.student_a_id}/ban",
            json={"reason": "Individual policy violation"},
        )

        self.assertEqual(response.status_code, 200)

        with Session(self.engine) as session:
            stored = session.exec(
                select(RefreshSession).where(
                    RefreshSession.token_hash
                    == "individual-active-token"
                )
            ).one()
            self.assertIsNotNone(stored.revoked_at)


if __name__ == "__main__":
    unittest.main()
