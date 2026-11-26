import json
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.admin.router import router as admin_router
from app.auth.dependencies import get_current_admin
from app.auth.permissions import ADMIN, require_user_role
from app.models.audit_log import AuditLog
from app.models.group import Group, GroupMember
from app.models.service_request import ServiceRequest
from app.models.user import User
from database import get_session


class AdminGroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(cls.engine, "connect")
        def enable_foreign_keys(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

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

        self.admin_id = uuid4()
        self.owner_id = uuid4()
        self.member_id = uuid4()
        self.admin_active_group_id = uuid4()
        self.admin_archived_group_id = uuid4()
        self.active_group_with_request_id = uuid4()
        self.archived_group_with_request_id = uuid4()
        self.request_id = 81001
        self.archived_request_id = 81002

        with Session(self.engine) as session:
            session.add_all(
                [
                    User(
                        id=self.admin_id,
                        email="admin-groups@test.com",
                        name="Group Admin",
                        password_hash="test-hash",
                        role="ADMIN",
                    ),
                    User(
                        id=self.owner_id,
                        email="owner-groups@test.com",
                        name="Group Owner",
                        password_hash="test-hash",
                        role="STUDENT",
                    ),
                    User(
                        id=self.member_id,
                        email="member-groups@test.com",
                        name="Group Member",
                        password_hash="test-hash",
                        role="STUDENT",
                    ),
                ]
            )
            session.flush()
            session.add_all(
                [
                    Group(
                        id=self.admin_active_group_id,
                        name="Empty active group",
                        owner_id=self.owner_id,
                    ),
                    Group(
                        id=self.admin_archived_group_id,
                        name="Empty archived group",
                        owner_id=self.owner_id,
                        is_archived=True,
                    ),
                    Group(
                        id=self.active_group_with_request_id,
                        name="Active group with request",
                        owner_id=self.owner_id,
                    ),
                    Group(
                        id=self.archived_group_with_request_id,
                        name="Archived group with request",
                        owner_id=self.owner_id,
                        is_archived=True,
                    ),
                ]
            )
            session.flush()
            session.add(
                GroupMember(
                    group_id=self.admin_active_group_id,
                    user_id=self.member_id,
                )
            )
            session.add_all(
                [
                    ServiceRequest(
                        id=self.request_id,
                        user_id=self.owner_id,
                        group_id=self.active_group_with_request_id,
                        title="Active request",
                        description="Request description",
                        category="Facilities",
                    ),
                    ServiceRequest(
                        id=self.archived_request_id,
                        user_id=self.owner_id,
                        group_id=self.archived_group_with_request_id,
                        title="Archived request",
                        description="Request description",
                        category="Facilities",
                    ),
                ]
            )
            session.commit()

        type(self).current_admin_id = self.admin_id

    def login_as(self, user_id):
        type(self).current_admin_id = user_id

    def get_group(self, group_id):
        with Session(self.engine) as session:
            return session.get(Group, group_id)

    def get_audit_logs(self, action):
        with Session(self.engine) as session:
            statement = select(AuditLog).where(AuditLog.action == action)
            return list(session.exec(statement).all())

    def get_group_members(self, group_id):
        with Session(self.engine) as session:
            statement = select(GroupMember).where(
                GroupMember.group_id == group_id
            )
            return list(session.exec(statement).all())

    def test_group_list_includes_owner_counts_and_archive_metadata(self):
        response = self.client.get(
            "/api/admin/groups",
            params={"page": 1, "page_size": 2},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 4)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 2)
        self.assertEqual(body["total_pages"], 2)

        groups = {
            group["id"]: group
            for group in self.client.get(
                "/api/admin/groups",
                params={"page": 1, "page_size": 100},
            ).json()["groups"]
        }
        active = groups[str(self.admin_active_group_id)]
        self.assertEqual(active["owner_id"], str(self.owner_id))
        self.assertEqual(active["owner_name"], "Group Owner")
        self.assertEqual(active["owner_email"], "owner-groups@test.com")
        self.assertEqual(active["member_count"], 2)
        self.assertEqual(active["request_count"], 0)
        self.assertFalse(active["is_archived"])
        self.assertIsNotNone(active["created_at"])
        self.assertIsNotNone(active["updated_at"])

        protected = groups[str(self.archived_group_with_request_id)]
        self.assertEqual(protected["request_count"], 1)
        self.assertTrue(protected["is_archived"])

    def test_group_routes_require_an_admin(self):
        type(self).current_admin_id = None
        response = self.client.get("/api/admin/groups")
        self.assertEqual(response.status_code, 401)

        self.login_as(self.owner_id)
        response = self.client.get("/api/admin/groups")
        self.assertEqual(response.status_code, 403)

        response = self.client.delete(
            f"/api/admin/groups/{self.admin_active_group_id}"
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            "/api/admin/groups/bulk-delete",
            json={"group_ids": [str(self.admin_active_group_id)]},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_empty_active_and_archived_groups(self):
        for group_id in (
            self.admin_active_group_id,
            self.admin_archived_group_id,
        ):
            with self.subTest(group_id=group_id):
                response = self.client.delete(
                    f"/api/admin/groups/{group_id}"
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["success"])
                self.assertEqual(response.json()["group_id"], str(group_id))
                self.assertIsNone(self.get_group(group_id))
                self.assertEqual(self.get_group_members(group_id), [])

        audit_logs = self.get_audit_logs("GROUP_DELETED")
        self.assertEqual(len(audit_logs), 2)
        self.assertTrue(
            all(log.actor_id == self.admin_id for log in audit_logs)
        )
        details = [json.loads(log.details) for log in audit_logs]
        self.assertEqual(
            {item["group_id"] for item in details},
            {
                str(self.admin_active_group_id),
                str(self.admin_archived_group_id),
            },
        )

    def test_admin_cannot_delete_groups_containing_requests(self):
        for group_id in (
            self.active_group_with_request_id,
            self.archived_group_with_request_id,
        ):
            with self.subTest(group_id=group_id):
                response = self.client.delete(
                    f"/api/admin/groups/{group_id}"
                )
                self.assertEqual(response.status_code, 409)
                self.assertIsNotNone(self.get_group(group_id))

        self.assertEqual(self.get_audit_logs("GROUP_DELETED"), [])

    def test_delete_missing_group_returns_not_found(self):
        response = self.client.delete(f"/api/admin/groups/{uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_bulk_delete_returns_independent_result_for_every_group(self):
        missing_id = uuid4()
        requested_ids = [
            self.admin_active_group_id,
            self.active_group_with_request_id,
            missing_id,
            self.admin_archived_group_id,
            self.archived_group_with_request_id,
        ]

        response = self.client.post(
            "/api/admin/groups/bulk-delete",
            json={"group_ids": [str(group_id) for group_id in requested_ids]},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 5)
        self.assertEqual(body["succeeded"], 2)
        self.assertEqual(body["failed"], 3)
        results = {
            result["group_id"]: result
            for result in body["results"]
        }
        self.assertEqual(
            list(results),
            [str(group_id) for group_id in requested_ids],
        )
        self.assertTrue(results[str(self.admin_active_group_id)]["success"])
        self.assertTrue(results[str(self.admin_archived_group_id)]["success"])
        self.assertFalse(
            results[str(self.active_group_with_request_id)]["success"]
        )
        self.assertEqual(
            results[str(self.active_group_with_request_id)]["message"],
            "Cannot delete a group containing service requests.",
        )
        self.assertFalse(results[str(missing_id)]["success"])
        self.assertEqual(results[str(missing_id)]["message"], "Group not found.")
        self.assertFalse(
            results[str(self.archived_group_with_request_id)]["success"]
        )
        self.assertIsNone(self.get_group(self.admin_active_group_id))
        self.assertIsNone(self.get_group(self.admin_archived_group_id))
        self.assertIsNotNone(
            self.get_group(self.active_group_with_request_id)
        )
        self.assertEqual(len(self.get_audit_logs("GROUP_DELETED")), 2)

    def test_bulk_delete_rolls_back_integrity_failure_and_continues(self):
        with patch(
            "app.admin.service.get_admin_group_request_count",
            return_value=0,
        ):
            response = self.client.post(
                "/api/admin/groups/bulk-delete",
                json={
                    "group_ids": [
                        str(self.active_group_with_request_id),
                        str(self.admin_archived_group_id),
                    ]
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["succeeded"], 1)
        self.assertEqual(body["failed"], 1)
        self.assertIsNotNone(
            self.get_group(self.active_group_with_request_id)
        )
        self.assertIsNone(self.get_group(self.admin_archived_group_id))
        results = {item["group_id"]: item for item in body["results"]}
        self.assertEqual(
            results[str(self.active_group_with_request_id)]["message"],
            "The group has related records and cannot be deleted.",
        )
        self.assertEqual(len(self.get_audit_logs("GROUP_DELETED")), 1)

    def test_audit_failure_rolls_back_group_deletion(self):
        with patch(
            "app.admin.service.record_event",
            side_effect=SQLAlchemyError("simulated audit failure"),
        ):
            response = self.client.delete(
                f"/api/admin/groups/{self.admin_active_group_id}"
            )

        self.assertEqual(response.status_code, 500)
        self.assertIsNotNone(self.get_group(self.admin_active_group_id))
        self.assertEqual(self.get_audit_logs("GROUP_DELETED"), [])

    def test_post_commit_refresh_failure_does_not_report_delete_failure(self):
        original_commit = Session.commit
        original_refresh = Session.refresh

        def track_commit(session):
            result = original_commit(session)
            session.info["commit_completed"] = True
            return result

        def fail_refresh_after_commit(session, *args, **kwargs):
            if session.info.get("commit_completed"):
                raise SQLAlchemyError(
                    "simulated post-commit refresh failure"
                )
            return original_refresh(session, *args, **kwargs)

        with (
            patch.object(Session, "commit", track_commit),
            patch.object(Session, "refresh", fail_refresh_after_commit),
        ):
            response = self.client.delete(
                f"/api/admin/groups/{self.admin_active_group_id}"
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertIsNone(self.get_group(self.admin_active_group_id))
        self.assertEqual(len(self.get_audit_logs("GROUP_DELETED")), 1)

    def test_bulk_delete_rejects_duplicate_and_oversized_batches(self):
        duplicate_response = self.client.post(
            "/api/admin/groups/bulk-delete",
            json={
                "group_ids": [
                    str(self.admin_active_group_id),
                    str(self.admin_active_group_id),
                ]
            },
        )
        self.assertEqual(duplicate_response.status_code, 422)

        oversized_response = self.client.post(
            "/api/admin/groups/bulk-delete",
            json={"group_ids": [str(uuid4()) for _ in range(101)]},
        )
        self.assertEqual(oversized_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
