
import unittest
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.user import User
from app.models.service_request import ServiceRequest
from app.models.group import Group, GroupMember
from app.service_requests.router import router as request_router
from app.staff.router import router as staff_router
from app.groups.router import router as group_router
from app.auth.dependencies import get_current_user
from database import get_session


class GroupAuthorizationTests(unittest.TestCase):

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
        cls.app.include_router(group_router)
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

        cls.app.dependency_overrides[get_current_user] = override_get_current_user
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

        self.owner_id = uuid4()
        self.member_create_id = uuid4()
        self.member_edit_id = uuid4()
        self.member_assign_id = uuid4()
        self.member_none_id = uuid4()
        self.non_member_id = uuid4()
        self.staff_id = uuid4()
        self.admin_id = uuid4()

        self.group_id = uuid4()
        self.archived_group_id = uuid4()
        self.empty_group_id = uuid4()
        self.second_group_id = uuid4()

        self.group_request_id = 100
        self.assigned_group_request_id = 101
        self.personal_request_id = 102
        self.archived_group_request_id = 103
        self.second_group_request_id = 104

        users = [
            User(
                id=self.owner_id,
                email="owner@test.com",
                name="Group Owner",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.member_create_id,
                email="member_create@test.com",
                name="Member Create",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.member_edit_id,
                email="member_edit@test.com",
                name="Member Edit",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.member_assign_id,
                email="member_assign@test.com",
                name="Member Assign",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.member_none_id,
                email="member_none@test.com",
                name="Member None",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.non_member_id,
                email="non_member@test.com",
                name="Non Member",
                password_hash="test-hash",
                role="STUDENT",
            ),
            User(
                id=self.staff_id,
                email="staff@test.com",
                name="Staff Member",
                password_hash="test-hash",
                role="STAFF",
            ),
            User(
                id=self.admin_id,
                email="admin@test.com",
                name="Admin User",
                password_hash="test-hash",
                role="ADMIN",
            ),
        ]

        with Session(self.engine) as session:
            session.add_all(users)
            session.commit()

            active_group = Group(
                id=self.group_id,
                name="Robotics Club",
                description="Robotics laboratory service group",
                owner_id=self.owner_id,
                is_archived=False,
            )

            archived_group = Group(
                id=self.archived_group_id,
                name="Past Project",
                description="Archived semester project group",
                owner_id=self.owner_id,
                is_archived=True,
            )

            empty_group = Group(
                id=self.empty_group_id,
                name="Empty Group",
                description="Temporary group with no requests",
                owner_id=self.owner_id,
                is_archived=False,
            )

            second_group = Group(
                id=self.second_group_id,
                name="Engineering Club",
                description="Second test group",
                owner_id=self.owner_id,
                is_archived=False,
            )

            session.add_all([
                active_group,
                archived_group,
                empty_group,
                second_group,
            ])
            session.commit()

            memberships = [
                GroupMember(
                    id=uuid4(),
                    group_id=self.group_id,
                    user_id=self.member_create_id,
                    can_create_requests=True,
                    can_edit_requests=False,
                    can_assign_requests=False,
                ),
                GroupMember(
                    id=uuid4(),
                    group_id=self.group_id,
                    user_id=self.member_edit_id,
                    can_create_requests=False,
                    can_edit_requests=True,
                    can_assign_requests=False,
                ),
                GroupMember(
                    id=uuid4(),
                    group_id=self.group_id,
                    user_id=self.member_assign_id,
                    can_create_requests=False,
                    can_edit_requests=False,
                    can_assign_requests=True,
                ),
                GroupMember(
                    id=uuid4(),
                    group_id=self.group_id,
                    user_id=self.member_none_id,
                    can_create_requests=False,
                    can_edit_requests=False,
                    can_assign_requests=False,
                ),
                GroupMember(
                    id=uuid4(),
                    group_id=self.archived_group_id,
                    user_id=self.member_create_id,
                    can_create_requests=True,
                    can_edit_requests=True,
                    can_assign_requests=True,
                ),
            ]

            session.add_all(memberships)
            session.commit()

            group_req = ServiceRequest(
                id=self.group_request_id,
                user_id=self.owner_id,
                group_id=self.group_id,
                title="Broken Robot Sensor",
                description="Sensor in lab needs calibration",
                category="Equipment",
                status="pending",
            )

            assigned_group_req = ServiceRequest(
                id=self.assigned_group_request_id,
                user_id=self.owner_id,
                group_id=self.group_id,
                assigned_to=self.staff_id,
                title="Lab Power Outlet",
                description="Wall socket not functioning",
                category="Electrical",
                status="assigned",
            )

            personal_req = ServiceRequest(
                id=self.personal_request_id,
                user_id=self.owner_id,
                group_id=None,
                title="Dorm Lamp",
                description="Personal dorm lamp flicker",
                category="Electrical",
                status="pending",
            )

            archived_group_req = ServiceRequest(
                id=self.archived_group_request_id,
                user_id=self.owner_id,
                group_id=self.archived_group_id,
                title="Archived Project Equipment",
                description="Equipment request from a completed project",
                category="Equipment",
                status="pending",
            )

            second_group_req = ServiceRequest(
                id=self.second_group_request_id,
                user_id=self.owner_id,
                group_id=self.second_group_id,
                title="Second Group Request",
                description="Request belonging to the second group",
                category="Equipment",
                status="pending",
            )

            session.add_all([
                group_req,
                assigned_group_req,
                personal_req,
                archived_group_req,
                second_group_req,
            ])
            session.commit()

        self.login_as(self.owner_id)

    def login_as(self, user_id):
        type(self).current_user_id = user_id

    # GROUP CREATION & OWNERSHIP TESTS

    def test_create_group_sets_owner_and_full_permissions(self):
        self.login_as(self.owner_id)

        response = self.client.post(
            "/api/groups",
            json={
                "name": "AI Study Group",
                "description": "Collaboration on machine learning hardware",
            },
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["name"], "AI Study Group")
        self.assertEqual(data["owner_id"], str(self.owner_id))
        self.assertTrue(data["is_owner"])
        self.assertTrue(data["permissions"]["can_create_requests"])
        self.assertTrue(data["permissions"]["can_edit_requests"])
        self.assertTrue(data["permissions"]["can_assign_requests"])

    def test_owner_can_rename_group(self):
        self.login_as(self.owner_id)

        response = self.client.patch(
            "/api/groups/{}".format(self.group_id),
            json={"name": "Renamed Robotics Lab"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Renamed Robotics Lab")

    def test_member_cannot_rename_group(self):
        self.login_as(self.member_create_id)

        response = self.client.patch(
            "/api/groups/{}".format(self.group_id),
            json={"name": "Unauthorized Name Change"},
        )

        self.assertEqual(response.status_code, 403)

    def test_non_member_cannot_rename_group(self):
        self.login_as(self.non_member_id)

        response = self.client.patch(
            "/api/groups/{}".format(self.group_id),
            json={"name": "Non Member Rename"},
        )

        self.assertEqual(response.status_code, 404)

    def test_owner_can_archive_and_unarchive_group(self):
        self.login_as(self.owner_id)

        archive_res = self.client.post(
            "/api/groups/{}/archive".format(self.group_id)
        )

        self.assertEqual(archive_res.status_code, 200)
        self.assertTrue(archive_res.json()["is_archived"])

        unarchive_res = self.client.post(
            "/api/groups/{}/unarchive".format(self.group_id)
        )

        self.assertEqual(unarchive_res.status_code, 200)
        self.assertFalse(unarchive_res.json()["is_archived"])

    def test_owner_can_delete_empty_group(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}".format(self.empty_group_id)
        )

        self.assertEqual(response.status_code, 200)

        check_res = self.client.get(
            "/api/groups/{}".format(self.empty_group_id)
        )

        self.assertEqual(check_res.status_code, 404)

    def test_owner_cannot_delete_group_with_requests(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}".format(self.group_id)
        )

        self.assertEqual(response.status_code, 400)

        self.assertIn(
            "Cannot delete group containing service requests",
            response.json()["detail"],
        )

    def test_member_cannot_delete_group(self):
        self.login_as(self.member_create_id)

        response = self.client.delete(
            "/api/groups/{}".format(self.empty_group_id)
        )

        self.assertEqual(response.status_code, 404)

        response2 = self.client.delete(
            "/api/groups/{}".format(self.group_id)
        )

        self.assertEqual(response2.status_code, 403)

    # MEMBER MANAGEMENT TESTS

    def test_add_member_defaults_all_permissions_to_false(self):
        self.login_as(self.owner_id)

        response = self.client.post(
            "/api/groups/{}/members".format(self.group_id),
            json={"email": "non_member@test.com"},
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["user_email"], "non_member@test.com")
        self.assertFalse(data["can_create_requests"])
        self.assertFalse(data["can_edit_requests"])
        self.assertFalse(data["can_assign_requests"])
        self.assertFalse(data["is_owner"])

    def test_cannot_add_owner_as_member(self):
        self.login_as(self.owner_id)

        response = self.client.post(
            "/api/groups/{}/members".format(self.group_id),
            json={"email": "owner@test.com"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("already the group owner", response.json()["detail"])

    def test_cannot_add_duplicate_member(self):
        self.login_as(self.owner_id)

        response = self.client.post(
            "/api/groups/{}/members".format(self.group_id),
            json={"email": "member_create@test.com"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("already a member", response.json()["detail"])

    def test_add_member_nonexistent_email_returns_404(self):
        self.login_as(self.owner_id)

        response = self.client.post(
            "/api/groups/{}/members".format(self.group_id),
            json={"email": "nonexistent@test.com"},
        )

        self.assertEqual(response.status_code, 404)

    def test_non_owner_cannot_add_member(self):
        self.login_as(self.member_create_id)

        response = self.client.post(
            "/api/groups/{}/members".format(self.group_id),
            json={"email": "non_member@test.com"},
        )

        self.assertEqual(response.status_code, 403)

    def test_owner_can_update_member_permissions(self):
        self.login_as(self.owner_id)

        response = self.client.patch(
            "/api/groups/{}/members/{}".format(
                self.group_id,
                self.member_none_id,
            ),
            json={
                "can_create_requests": True,
                "can_edit_requests": True,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["can_create_requests"])
        self.assertTrue(data["can_edit_requests"])
        self.assertFalse(data["can_assign_requests"])

    def test_non_owner_cannot_update_member_permissions(self):
        self.login_as(self.member_create_id)

        response = self.client.patch(
            "/api/groups/{}/members/{}".format(
                self.group_id,
                self.member_none_id,
            ),
            json={"can_create_requests": True},
        )

        self.assertEqual(response.status_code, 403)

    def test_cannot_update_owner_permissions_via_member_endpoint(self):
        self.login_as(self.owner_id)

        response = self.client.patch(
            "/api/groups/{}/members/{}".format(
                self.group_id,
                self.owner_id,
            ),
            json={"can_create_requests": False},
        )

        self.assertEqual(response.status_code, 400)

        self.assertIn(
            "Cannot modify permissions of the group owner",
            response.json()["detail"],
        )

    def test_owner_can_remove_member_and_revocation_is_immediate(self):
        self.login_as(self.owner_id)

        remove_res = self.client.delete(
            "/api/groups/{}/members/{}".format(
                self.group_id,
                self.member_edit_id,
            )
        )

        self.assertEqual(remove_res.status_code, 200)

        self.login_as(self.member_edit_id)

        group_res = self.client.get(
            "/api/groups/{}".format(self.group_id)
        )
        self.assertEqual(group_res.status_code, 404)

        request_res = self.client.get(
            "/api/requests/{}".format(self.group_request_id)
        )
        self.assertEqual(request_res.status_code, 404)

        edit_res = self.client.put(
            "/api/requests/{}".format(self.group_request_id),
            json={
                "title": "Unauthorized after removal",
                "description": "Removed member should not edit this request",
                "category": "Equipment",
                "status": "pending",
            },
        )
        self.assertIn(edit_res.status_code, [403, 404])

        delete_res = self.client.delete(
            "/api/requests/{}".format(self.group_request_id)
        )
        self.assertIn(delete_res.status_code, [403, 404])

    def test_owner_cannot_remove_self_from_members(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}/members/{}".format(
                self.group_id,
                self.owner_id,
            )
        )

        self.assertEqual(response.status_code, 400)

        self.assertIn(
            "Group owner cannot leave the group",
            response.json()["detail"],
        )

    def test_member_can_leave_group(self):
        self.login_as(self.member_edit_id)

        response = self.client.delete(
            "/api/groups/{}/members/{}".format(
                self.group_id,
                self.member_edit_id,
            )
        )

        self.assertEqual(response.status_code, 200)

        access_res = self.client.get(
            "/api/groups/{}".format(self.group_id)
        )

        self.assertEqual(access_res.status_code, 404)

    # FINE-GRAINED PERMISSION ENFORCEMENT TESTS

    def test_member_with_create_permission_can_create_group_request(self):
        self.login_as(self.member_create_id)

        response = self.client.post(
            "/api/groups/{}/requests".format(self.group_id),
            json={
                "title": "New Multimeter Needed",
                "description": "Workbench 4 requires calibrated multimeter",
                "category": "Equipment",
            },
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertEqual(data["title"], "New Multimeter Needed")
        self.assertEqual(data["group_id"], str(self.group_id))

    def test_member_without_create_permission_cannot_create_group_request(self):
        self.login_as(self.member_none_id)

        response = self.client.post(
            "/api/groups/{}/requests".format(self.group_id),
            json={
                "title": "Unauthorized Request",
                "description": "Trying to create without permission",
                "category": "Equipment",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_member_with_edit_permission_can_edit_group_request(self):
        self.login_as(self.member_edit_id)

        response = self.client.put(
            "/api/groups/{}/requests/{}".format(
                self.group_id,
                self.group_request_id,
            ),
            json={
                "title": "Updated Sensor Title",
                "description": "Updated sensor description with details",
                "category": "Equipment",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Updated Sensor Title")

    def test_member_without_edit_permission_cannot_edit_group_request(self):
        self.login_as(self.member_none_id)

        response = self.client.put(
            "/api/groups/{}/requests/{}".format(
                self.group_id,
                self.group_request_id,
            ),
            json={
                "title": "Forbidden Edit",
                "description": "Trying to edit without permission",
                "category": "Equipment",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_group_edit_cannot_change_protected_fields(self):
        self.login_as(self.member_edit_id)

        response = self.client.put(
            "/api/groups/{}/requests/{}".format(
                self.group_id,
                self.group_request_id,
            ),
            json={
                "title": "Safe Updated Title",
                "description": "Safe updated description",
                "category": "Equipment",
                "user_id": str(self.member_edit_id),
                "group_id": str(self.second_group_id),
                "assigned_to": str(self.staff_id),
                "status": "resolved",
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["user_id"], str(self.owner_id))
        self.assertEqual(data["group_id"], str(self.group_id))
        self.assertIsNone(data["assigned_to"])
        self.assertEqual(data["status"], "pending")

    def test_standard_group_edit_cannot_change_protected_fields(self):
        self.login_as(self.member_edit_id)

        response = self.client.put(
            "/api/requests/{}".format(self.group_request_id),
            json={
                "title": "Safe Standard Updated Title",
                "description": "Safe standard updated description",
                "category": "Equipment",
                "status": "resolved",
                "user_id": str(self.member_edit_id),
                "group_id": str(self.second_group_id),
                "assigned_to": str(self.staff_id),
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["user_id"], str(self.owner_id))
        self.assertEqual(data["group_id"], str(self.group_id))
        self.assertIsNone(data["assigned_to"])
        self.assertEqual(data["status"], "pending")

    def test_member_cannot_delete_group_request_regardless_of_permissions(self):
        for member_id in [
            self.member_create_id,
            self.member_edit_id,
            self.member_assign_id,
        ]:
            self.login_as(member_id)

            response = self.client.delete(
                "/api/groups/{}/requests/{}".format(
                    self.group_id,
                    self.group_request_id,
                )
            )

            self.assertEqual(response.status_code, 403)

    def test_owner_can_delete_pending_group_request(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}/requests/{}".format(
                self.group_id,
                self.group_request_id,
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_member_with_assign_permission_can_assign_staff(self):
        self.login_as(self.member_assign_id)

        response = self.client.patch(
            "/api/groups/{}/requests/{}/assign".format(
                self.group_id,
                self.group_request_id,
            ),
            json={"staff_id": str(self.staff_id)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "assigned")
        self.assertEqual(response.json()["assigned_to"], str(self.staff_id))

    def test_member_without_assign_permission_cannot_assign_staff(self):
        self.login_as(self.member_none_id)

        response = self.client.patch(
            "/api/groups/{}/requests/{}/assign".format(
                self.group_id,
                self.group_request_id,
            ),
            json={"staff_id": str(self.staff_id)},
        )

        self.assertEqual(response.status_code, 403)

    # CROSS-GROUP REQUEST ISOLATION TESTS

    def test_group_a_request_cannot_be_retrieved_through_group_b(self):
        self.login_as(self.owner_id)

        response = self.client.get(
            "/api/groups/{}/requests/{}".format(
                self.second_group_id,
                self.group_request_id,
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_group_a_request_cannot_be_edited_through_group_b(self):
        self.login_as(self.owner_id)

        response = self.client.put(
            "/api/groups/{}/requests/{}".format(
                self.second_group_id,
                self.group_request_id,
            ),
            json={
                "title": "Cross Group Edit",
                "description": "This should not change Group A request",
                "category": "Equipment",
            },
        )

        self.assertEqual(response.status_code, 404)

    def test_group_a_request_cannot_be_deleted_through_group_b(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}/requests/{}".format(
                self.second_group_id,
                self.group_request_id,
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_group_a_request_cannot_be_assigned_through_group_b(self):
        self.login_as(self.owner_id)

        response = self.client.patch(
            "/api/groups/{}/requests/{}/assign".format(
                self.second_group_id,
                self.group_request_id,
            ),
            json={"staff_id": str(self.staff_id)},
        )

        self.assertEqual(response.status_code, 404)

    def test_group_a_request_cannot_be_unassigned_through_group_b(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}/requests/{}/assign".format(
                self.second_group_id,
                self.assigned_group_request_id,
            )
        )

        self.assertEqual(response.status_code, 404)

    # STAFF ISOLATION TESTS

    def test_assigned_staff_can_retrieve_exact_assigned_request(self):
        self.login_as(self.staff_id)

        response = self.client.get(
            "/api/requests/{}".format(self.assigned_group_request_id)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["id"],
            self.assigned_group_request_id,
        )

    def test_assigned_staff_cannot_retrieve_unassigned_group_request(self):
        self.login_as(self.staff_id)

        response = self.client.get(
            "/api/requests/{}".format(self.group_request_id)
        )

        self.assertEqual(response.status_code, 404)

    def test_assigned_staff_cannot_retrieve_unrelated_group_request(self):
        self.login_as(self.staff_id)

        response = self.client.get(
            "/api/requests/{}".format(self.second_group_request_id)
        )

        self.assertEqual(response.status_code, 404)

    def test_assigned_staff_can_retrieve_exact_request_through_group_endpoint(self):
        self.login_as(self.staff_id)

        response = self.client.get(
            "/api/groups/{}/requests/{}".format(
                self.group_id,
                self.assigned_group_request_id,
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_assigned_staff_cannot_retrieve_unassigned_request_through_group_endpoint(self):
        self.login_as(self.staff_id)

        response = self.client.get(
            "/api/groups/{}/requests/{}".format(
                self.group_id,
                self.group_request_id,
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_assigned_staff_cannot_access_group_endpoint_or_roster(self):
        self.login_as(self.staff_id)

        group_res = self.client.get(
            "/api/groups/{}".format(self.group_id)
        )
        self.assertEqual(group_res.status_code, 404)

        members_res = self.client.get(
            "/api/groups/{}/members".format(self.group_id)
        )
        self.assertEqual(members_res.status_code, 404)

        requests_res = self.client.get(
            "/api/groups/{}/requests".format(self.group_id)
        )
        self.assertEqual(requests_res.status_code, 404)

    # ARCHIVED GROUP IMMUTABILITY TESTS

    def test_archived_group_blocks_all_mutations(self):
        self.login_as(self.owner_id)

        create_res = self.client.post(
            "/api/groups/{}/requests".format(self.archived_group_id),
            json={
                "title": "New Request in Archived",
                "description": "Should fail",
                "category": "Other",
            },
        )

        self.assertEqual(create_res.status_code, 400)
        self.assertIn("Group is archived", create_res.json()["detail"])

        add_member_res = self.client.post(
            "/api/groups/{}/members".format(self.archived_group_id),
            json={"email": "non_member@test.com"},
        )

        self.assertEqual(add_member_res.status_code, 400)

        rename_res = self.client.patch(
            "/api/groups/{}".format(self.archived_group_id),
            json={"name": "New Name Archived"},
        )

        self.assertEqual(rename_res.status_code, 400)

    def test_archived_group_blocks_member_request_edit(self):
        self.login_as(self.member_create_id)

        response = self.client.put(
            "/api/groups/{}/requests/{}".format(
                self.archived_group_id,
                self.archived_group_request_id,
            ),
            json={
                "title": "Unauthorized Archived Edit",
                "description": "This edit should be rejected",
                "category": "Equipment",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Group is archived", response.json()["detail"])

    def test_archived_group_blocks_staff_assignment(self):
        self.login_as(self.member_create_id)

        response = self.client.patch(
            "/api/groups/{}/requests/{}/assign".format(
                self.archived_group_id,
                self.archived_group_request_id,
            ),
            json={"staff_id": str(self.staff_id)},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Group is archived", response.json()["detail"])

    def test_owner_cannot_delete_archived_empty_group(self):
        self.login_as(self.owner_id)

        response = self.client.delete(
            "/api/groups/{}".format(self.archived_group_id)
        )

        self.assertEqual(response.status_code, 400)

        self.assertIn(
            "Group is archived",
            response.json()["detail"],
        )

        check_res = self.client.get(
            "/api/groups/{}".format(self.archived_group_id)
        )

        self.assertEqual(check_res.status_code, 200)
        self.assertTrue(check_res.json()["is_archived"])

    # PERSONAL REQUEST ISOLATION TESTS

    def test_personal_requests_endpoint_excludes_group_requests(self):
        self.login_as(self.owner_id)

        response = self.client.get("/api/requests")

        self.assertEqual(response.status_code, 200)

        request_ids = [r["id"] for r in response.json()]

        self.assertIn(self.personal_request_id, request_ids)
        self.assertNotIn(self.group_request_id, request_ids)
        self.assertNotIn(self.assigned_group_request_id, request_ids)

    # ADMIN ACCESS POLICY TESTS

    def test_admin_can_retrieve_individual_group_request(self):
        self.login_as(self.admin_id)

        response = self.client.get(
            "/api/requests/{}".format(self.group_request_id)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.group_request_id)

    def test_admin_cannot_access_private_group_resources(self):
        self.login_as(self.admin_id)

        group_res = self.client.get(
            "/api/groups/{}".format(self.group_id)
        )
        self.assertEqual(group_res.status_code, 404)

        members_res = self.client.get(
            "/api/groups/{}/members".format(self.group_id)
        )
        self.assertEqual(members_res.status_code, 404)

        requests_res = self.client.get(
            "/api/groups/{}/requests".format(self.group_id)
        )
        self.assertEqual(requests_res.status_code, 404)

    # NON-MEMBER ACCESS PRIVACY TESTS

    def test_non_member_cannot_view_group_or_requests(self):
        self.login_as(self.non_member_id)

        group_res = self.client.get(
            "/api/groups/{}".format(self.group_id)
        )
        self.assertEqual(group_res.status_code, 404)

        requests_res = self.client.get(
            "/api/groups/{}/requests".format(self.group_id)
        )
        self.assertEqual(requests_res.status_code, 404)

        members_res = self.client.get(
            "/api/groups/{}/members".format(self.group_id)
        )
        self.assertEqual(members_res.status_code, 404)


if __name__ == "__main__":
    unittest.main()
