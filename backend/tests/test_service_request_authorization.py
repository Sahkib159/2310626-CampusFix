
import unittest
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.service_request import ServiceRequest
from app.service_requests.router import router as request_router
from app.staff.router import router as staff_router
from app.auth.dependencies import get_current_user
from database import get_session


class ServiceRequestAuthorizationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        cls.app = FastAPI()
        cls.app.include_router(request_router)
        cls.app.include_router(staff_router)
        cls.current_user_id = None

        def override_get_current_user():
            with Session(cls.engine) as session:
                user = session.get(User, cls.current_user_id)

                if user is None:
                    raise RuntimeError("Test user not found.")

                session.expunge(user)
                return user

        def override_get_session():
            with Session(cls.engine) as session:
                yield session

        cls.app.dependency_overrides[get_current_user] = (
            override_get_current_user
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
        # Give every test a fresh database state.
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

        self.student_a_id = uuid4()
        self.student_b_id = uuid4()
        self.staff_a_id = uuid4()
        self.staff_b_id = uuid4()
        self.admin_id = uuid4()

        self.request_a_id = 1
        self.request_b_id = 2
        self.active_group_id = uuid4()
        self.archived_group_id = uuid4()
        self.active_group_request_id = 3
        self.archived_group_request_id = 4

        users = [
            User(
                id=self.student_a_id,
                email="student_a@test.com",
                name="Student A",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.student_b_id,
                email="student_b@test.com",
                name="Student B",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.staff_a_id,
                email="staff_a@test.com",
                name="Staff A",
                password_hash="test-hash",
                role="STAFF",
            ),
            User(
                id=self.staff_b_id,
                email="staff_b@test.com",
                name="Staff B",
                password_hash="test-hash",
                role="STAFF",
            ),
            User(
                id=self.admin_id,
                email="admin@test.com",
                name="Admin",
                password_hash="test-hash",
                role="ADMIN",
            ),
        ]

        with Session(self.engine) as session:
            session.add_all(users)
            session.commit()

            active_group = Group(
                id=self.active_group_id,
                name="Active Group",
                description="Active test group",
                owner_id=self.student_a_id,
                is_archived=False,
            )

            archived_group = Group(
                id=self.archived_group_id,
                name="Archived Group",
                description="Archived test group",
                owner_id=self.student_a_id,
                is_archived=True,
            )

            session.add_all([active_group, archived_group])
            session.commit()

            memberships = [
                GroupMember(
                    id=uuid4(),
                    group_id=self.active_group_id,
                    user_id=self.student_b_id,
                    can_create_requests=False,
                    can_edit_requests=False,
                    can_assign_requests=False,
                ),
                GroupMember(
                    id=uuid4(),
                    group_id=self.active_group_id,
                    user_id=self.staff_a_id,
                    can_create_requests=False,
                    can_edit_requests=False,
                    can_assign_requests=True,
                ),
                GroupMember(
                    id=uuid4(),
                    group_id=self.archived_group_id,
                    user_id=self.staff_a_id,
                    can_create_requests=False,
                    can_edit_requests=False,
                    can_assign_requests=True,
                ),
            ]

            active_group_request = ServiceRequest(
                id=self.active_group_request_id,
                user_id=self.student_a_id,
                group_id=self.active_group_id,
                title="Active group request",
                description="Request belonging to active group",
                category="IT",
                status="pending",
            )

            archived_group_request = ServiceRequest(
                id=self.archived_group_request_id,
                user_id=self.student_a_id,
                group_id=self.archived_group_id,
                title="Archived group request",
                description="Request belonging to archived group",
                category="IT",
                status="pending",
            )

            session.add_all([
                *memberships,
                active_group_request,
                archived_group_request,
            ])
            session.commit()

            request_a = ServiceRequest(
                id=self.request_a_id,
                user_id=self.student_a_id,
                assigned_to=self.staff_a_id,
                title="Student A request",
                description="Request created by Student A",
                category="IT",
                status="pending",
            )

            request_b = ServiceRequest(
                id=self.request_b_id,
                user_id=self.student_b_id,
                assigned_to=self.staff_b_id,
                title="Student B request",
                description="Request created by Student B",
                category="Maintenance",
                status="pending",
            )

            session.add_all([request_a, request_b])
            session.commit()

        self.login_as(self.student_a_id)

    def login_as(self, user_id):
        type(self).current_user_id = user_id

    # STUDENT OWNERSHIP TESTS

    def test_student_can_view_own_request(self):
        self.login_as(self.student_a_id)

        response = self.client.get(
            f"/api/requests/{self.request_a_id}"
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_view_other_student_request(self):
        self.login_as(self.student_a_id)

        response = self.client.get(
            f"/api/requests/{self.request_b_id}"
        )

        self.assertEqual(response.status_code, 404)

    def test_student_list_contains_only_own_requests(self):
        self.login_as(self.student_a_id)

        response = self.client.get("/api/requests")

        self.assertEqual(response.status_code, 200)

        request_ids = [
            item["id"] for item in response.json()
        ]

        self.assertIn(self.request_a_id, request_ids)
        self.assertNotIn(self.request_b_id, request_ids)

    def test_student_can_update_own_pending_request(self):
        self.login_as(self.student_a_id)

        response = self.client.put(
            f"/api/requests/{self.request_a_id}",
            json={
                "title": "Updated Student A request",
                "description": "Updated request description",
                "category": "IT",
                "status": "pending",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["title"],
            "Updated Student A request",
        )

    def test_student_cannot_update_other_student_request(self):
        self.login_as(self.student_a_id)

        response = self.client.put(
            f"/api/requests/{self.request_b_id}",
            json={
                "title": "Unauthorized update",
                "description": "Trying to change another student's request",
                "category": "IT",
                "status": "pending",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_delete_other_student_request(self):
        self.login_as(self.student_a_id)

        response = self.client.delete(
            f"/api/requests/{self.request_b_id}"
        )

        self.assertEqual(response.status_code, 404)

    # STAFF ASSIGNMENT TESTS

    def test_staff_can_view_assigned_request(self):
        self.login_as(self.staff_a_id)

        response = self.client.get(
            f"/api/requests/{self.request_a_id}"
        )

        self.assertEqual(response.status_code, 200)

    def test_staff_cannot_view_unassigned_request(self):
        self.login_as(self.staff_a_id)

        response = self.client.get(
            f"/api/requests/{self.request_b_id}"
        )

        self.assertEqual(response.status_code, 404)

    def test_staff_can_update_assigned_request_status(self):
        self.login_as(self.staff_a_id)

        response = self.client.put(
            f"/api/requests/{self.request_a_id}",
            json={
                "title": "Student A request",
                "description": "Request created by Student A",
                "category": "IT",
                "status": "in_progress",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "in_progress")

    def test_staff_cannot_update_unassigned_request(self):
        self.login_as(self.staff_a_id)

        response = self.client.put(
            f"/api/requests/{self.request_b_id}",
            json={
                "title": "Unauthorized update",
                "description": "Trying to update an unassigned request",
                "category": "IT",
                "status": "in_progress",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_staff_cannot_delete_assigned_request(self):
        self.login_as(self.staff_a_id)

        response = self.client.delete(
            f"/api/requests/{self.request_a_id}"
        )

        self.assertEqual(response.status_code, 403)

    def test_nonmember_cannot_assign_existing_or_nonexistent_group_requests(self):
        self.login_as(self.staff_b_id)

        for request_id in [
            self.active_group_request_id,
            self.archived_group_request_id,
            999,
        ]:
            with self.subTest(request_id=request_id):
                response = self.client.patch(
                    f"/api/requests/{request_id}/assign",
                    json={"staff_id": str(self.staff_a_id)},
                )
                self.assertEqual(response.status_code, 404)

    def test_nonmember_cannot_unassign_existing_or_nonexistent_group_requests(self):
        self.login_as(self.staff_b_id)

        for request_id in [
            self.active_group_request_id,
            self.archived_group_request_id,
            999,
        ]:
            with self.subTest(request_id=request_id):
                response = self.client.delete(
                    f"/api/requests/{request_id}/assign"
                )
                self.assertEqual(response.status_code, 404)

    def test_member_without_assign_permission_cannot_assign_or_unassign(self):
        self.login_as(self.student_b_id)

        for method in ["assign", "unassign"]:
            with self.subTest(method=method):
                if method == "assign":
                    response = self.client.patch(
                        f"/api/requests/{self.active_group_request_id}/assign",
                        json={"staff_id": str(self.staff_a_id)},
                    )
                else:
                    response = self.client.delete(
                        f"/api/requests/{self.active_group_request_id}/assign"
                    )

                self.assertEqual(response.status_code, 403)

    def test_owner_and_member_with_permission_can_assign_and_unassign(self):
        for user_id in [self.student_a_id, self.staff_a_id]:
            with self.subTest(user_id=user_id):
                self.login_as(user_id)

                assign_response = self.client.patch(
                    f"/api/requests/{self.active_group_request_id}/assign",
                    json={"staff_id": str(self.staff_a_id)},
                )
                self.assertEqual(assign_response.status_code, 200)

                unassign_response = self.client.delete(
                    f"/api/requests/{self.active_group_request_id}/assign"
                )
                self.assertEqual(unassign_response.status_code, 200)

    def test_archived_group_authorized_users_cannot_assign_or_unassign(self):
        for user_id in [self.student_a_id, self.staff_a_id]:
            with self.subTest(user_id=user_id):
                self.login_as(user_id)

                assign_response = self.client.patch(
                    f"/api/requests/{self.archived_group_request_id}/assign",
                    json={"staff_id": str(self.staff_a_id)},
                )
                self.assertEqual(assign_response.status_code, 400)

                unassign_response = self.client.delete(
                    f"/api/requests/{self.archived_group_request_id}/assign"
                )
                self.assertEqual(unassign_response.status_code, 400)

    # ADMIN ACCESS TESTS

    def test_admin_can_view_any_request(self):
        self.login_as(self.admin_id)

        response = self.client.get(
            f"/api/requests/{self.request_b_id}"
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_staff_endpoint(self):
        self.login_as(self.student_a_id)

        response = self.client.get("/api/staff")

        self.assertEqual(response.status_code, 403)

    def test_student_cannot_assign_staff(self):
        self.login_as(self.student_a_id)

        response = self.client.patch(
            f"/api/requests/{self.request_a_id}/assign",
            json={"staff_id": str(self.staff_b_id)},
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_assign_staff(self):
        self.login_as(self.staff_a_id)

        response = self.client.patch(
            f"/api/requests/{self.request_a_id}/assign",
            json={"staff_id": str(self.staff_b_id)},
        )

        self.assertEqual(response.status_code, 403)

    def test_admin_can_assign_staff(self):
        self.login_as(self.admin_id)

        response = self.client.patch(
            f"/api/requests/{self.request_a_id}/assign",
            json={"staff_id": str(self.staff_b_id)},
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_can_unassign_staff(self):
        self.login_as(self.admin_id)

        response = self.client.delete(
            f"/api/requests/{self.request_a_id}/assign"
        )

        self.assertEqual(response.status_code, 200)

        with Session(self.engine) as session:
            request = session.get(
                ServiceRequest,
                self.request_a_id,
            )

        self.assertIsNone(request.assigned_to)
        self.assertEqual(request.status, "pending")

    def test_admin_can_delete_another_student_request(self):
        self.login_as(self.admin_id)

        response = self.client.delete(
            f"/api/requests/{self.request_b_id}"
        )

        self.assertEqual(response.status_code, 200)

        with Session(self.engine) as session:
            deleted_request = session.get(
                ServiceRequest,
                self.request_b_id,
            )

        self.assertIsNone(deleted_request)


if __name__ == "__main__":
    unittest.main(verbosity=2)
