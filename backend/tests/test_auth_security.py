
import os
import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import patch

from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.user import User
from app.models.login_attempt import LoginAttempt
from app.models.refresh_session import RefreshSession
from app.models.service_request import ServiceRequest

from app.auth import service
from app.auth.schemas import LoginRequest
from app.auth.password import (
    hash_password,
    verify_password,
    password_hasher,
)
from app.auth.config import ACCESS_TOKEN_EXPIRE
from app.auth.jwt import create_access_token, decode_access_token
from app.auth.tokens import hash_refresh_token
from app.auth.dependencies import get_current_user
from database import get_session


class AuthenticationSecurityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)

        self.session = Session(self.engine)

        self.user = User(
            id=uuid4(),
            email="student@test.com",
            name="Test Student",
            password_hash="test-hash",
            role="STUDENT",
            is_active=True,
        )

        self.session.add(self.user)
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def login_data(self, email="student@test.com"):
        return LoginRequest(
            email=email,
            password="WrongPassword123",
        )

    # --------------------------------------------------
    # PASSWORD PEPPER TESTS
    # --------------------------------------------------

    def test_password_hash_uses_pepper(self):
        with patch.dict(
            os.environ,
            {"PASSWORD_PEPPER": "test-pepper"},
        ):
            hashed = hash_password("MyPassword123")

            self.assertTrue(
                hashed.startswith("pepper-v1$")
            )

            self.assertTrue(
                verify_password("MyPassword123", hashed)
            )

            self.assertFalse(
                verify_password("WrongPassword", hashed)
            )

    def test_legacy_password_is_upgraded_after_login(self):
        with patch.dict(
            os.environ,
            {"PASSWORD_PEPPER": "test-pepper"},
        ):
            legacy_hash = password_hasher.hash(
                "MyPassword123"
            )

            self.user.password_hash = legacy_hash
            self.session.add(self.user)
            self.session.commit()

            login_data = LoginRequest(
                email="student@test.com",
                password="MyPassword123",
            )

            with patch(
                "app.auth.repository.record_login_attempt"
            ):
                result = service.login(
                    self.session,
                    login_data,
                    "192.0.2.50",
                )

            self.session.refresh(self.user)

            self.assertTrue(
                self.user.password_hash.startswith(
                    "pepper-v1$"
                )
            )

            self.assertTrue(
                verify_password(
                    "MyPassword123",
                    self.user.password_hash,
                )
            )

            self.assertTrue(
                result["response"].access_token
            )

    # --------------------------------------------------
    # JWT TESTS
    # --------------------------------------------------

    def test_access_token_contains_user_id_and_role(self):
        token = create_access_token(
            self.user.id,
            self.user.role,
        )

        payload = decode_access_token(token)

        self.assertEqual(
            payload["sub"],
            str(self.user.id),
        )

        self.assertEqual(
            payload["role"],
            "STUDENT",
        )

        self.assertEqual(
            payload["type"],
            "access",
        )

    def test_access_token_expiry_matches_configured_limit(self):
        token = create_access_token(
            self.user.id,
            self.user.role,
        )

        payload = decode_access_token(token)

        issued_at = datetime.fromtimestamp(
            payload["iat"],
            timezone.utc,
        )

        expires_at = datetime.fromtimestamp(
            payload["exp"],
            timezone.utc,
        )

        lifetime = expires_at - issued_at

        self.assertLessEqual(
            lifetime,
            timedelta(minutes=15),
        )

        self.assertEqual(
            lifetime,
            ACCESS_TOKEN_EXPIRE,
        )

    # --------------------------------------------------
    # EMAIL RATE LIMIT TESTS
    # --------------------------------------------------

    @patch(
        "app.auth.service.verify_password",
        return_value=False,
    )
    def test_email_limit_after_five_failed_attempts(
        self,
        mock_verify,
    ):
        for _ in range(5):
            with self.assertRaises(ValueError):
                service.login(
                    self.session,
                    self.login_data(),
                    "192.0.2.10",
                )

        with self.assertRaises(
            service.LoginRateLimitError
        ):
            service.login(
                self.session,
                self.login_data(),
                "192.0.2.10",
            )

    # --------------------------------------------------
    # IP RATE LIMIT TESTS
    # --------------------------------------------------

    def test_ip_limit_after_twenty_failed_attempts(self):
        for number in range(20):
            email = f"unknown{number}@test.com"

            with self.assertRaises(ValueError):
                service.login(
                    self.session,
                    self.login_data(email),
                    "192.0.2.20",
                )

        with self.assertRaises(
            service.LoginRateLimitError
        ):
            service.login(
                self.session,
                self.login_data("another@test.com"),
                "192.0.2.20",
            )

    # --------------------------------------------------
    # FAILED LOGIN LOGGING
    # --------------------------------------------------

    def test_failed_login_is_recorded(self):
        with patch(
            "app.auth.service.verify_password",
            return_value=False,
        ):
            with self.assertRaises(ValueError):
                service.login(
                    self.session,
                    self.login_data(),
                    "192.0.2.30",
                )

        statement = select(LoginAttempt)
        attempts = self.session.exec(statement).all()

        self.assertEqual(len(attempts), 1)
        self.assertFalse(attempts[0].successful)

        self.assertEqual(
            attempts[0].email,
            "student@test.com",
        )

    # --------------------------------------------------
    # BANNED ACCOUNT LOGIN TEST
    # --------------------------------------------------

    @patch(
        "app.auth.service.verify_password",
        return_value=True,
    )
    def test_inactive_user_cannot_login(self, mock_verify):
        self.user.is_active = False
        self.session.add(self.user)
        self.session.commit()

        with patch(
            "app.auth.service.needs_password_upgrade",
            return_value=False,
        ):
            with self.assertRaises(ValueError):
                service.login(
                    self.session,
                    self.login_data(),
                    "192.0.2.40",
                )

        statement = select(LoginAttempt)
        attempts = self.session.exec(statement).all()

        self.assertEqual(len(attempts), 1)
        self.assertFalse(attempts[0].successful)

    # --------------------------------------------------
    # BANNED ACCOUNT ACCESS TEST
    # --------------------------------------------------

    def test_inactive_user_cannot_access_protected_endpoint(self):
        self.user.is_active = False
        self.session.add(self.user)
        self.session.commit()

        app = FastAPI()

        def override_get_session():
            yield self.session

        app.dependency_overrides[get_session] = (
            override_get_session
        )

        @app.get("/protected")
        def protected(
            current_user: User = Depends(get_current_user),
        ):
            return {"user_id": str(current_user.id)}

        token = create_access_token(
            self.user.id,
            self.user.role,
        )

        try:
            with TestClient(app) as client:
                response = client.get(
                    "/protected",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 403)

    # --------------------------------------------------
    # BANNED ACCOUNT REFRESH TOKEN TEST
    # --------------------------------------------------

    def test_inactive_user_refresh_token_is_revoked(self):
        self.user.is_active = False
        self.session.add(self.user)
        self.session.commit()

        raw_token = "test-refresh-token"
        family_id = uuid4()

        refresh_record = RefreshSession(
            user_id=self.user.id,
            family_id=family_id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

        self.session.add(refresh_record)
        self.session.commit()

        with self.assertRaises(ValueError):
            service.refresh_session(
                self.session,
                raw_token,
            )

        self.session.refresh(refresh_record)

        self.assertIsNotNone(
            refresh_record.revoked_at
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
