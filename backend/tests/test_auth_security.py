
import importlib
import jwt
import os
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import patch

from http.cookies import SimpleCookie
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel, Session, create_engine, select

from app.models.user import User
from app.models.login_attempt import LoginAttempt
from app.models.refresh_session import RefreshSession
from app.models.service_request import ServiceRequest

from app.auth import service
from app.auth import config
from app.auth import router as auth_router
from app.auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
)
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

    @contextmanager
    def temporary_cookie_secure(self, value):
        original_value = os.environ.get("COOKIE_SECURE")
        original_config_value = config.COOKIE_SECURE
        original_load_dotenv = config.load_dotenv

        try:
            if value is None:
                os.environ.pop("COOKIE_SECURE", None)
            else:
                os.environ["COOKIE_SECURE"] = value

            with patch("dotenv.load_dotenv"):
                importlib.reload(config)

            yield
        finally:
            if original_value is None:
                os.environ.pop("COOKIE_SECURE", None)
            else:
                os.environ["COOKIE_SECURE"] = original_value

            config.COOKIE_SECURE = original_config_value
            config.load_dotenv = original_load_dotenv

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
            self.user.token_version,
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

        self.assertEqual(
            payload["token_version"],
            0,
        )

    def test_access_token_expiry_matches_configured_limit(self):
        token = create_access_token(
            self.user.id,
            self.user.role,
            self.user.token_version,
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

    def test_access_token_requires_matching_token_version(self):
        matching_token = create_access_token(
            self.user.id,
            self.user.role,
            self.user.token_version,
        )

        current_user = get_current_user(
            HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=matching_token,
            ),
            self.session,
        )

        self.assertEqual(
            current_user.id,
            self.user.id,
        )

        self.user.token_version = 1
        self.session.add(self.user)
        self.session.commit()

        with self.assertRaises(HTTPException) as context:
            get_current_user(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=matching_token,
                ),
                self.session,
            )

        self.assertEqual(
            context.exception.status_code,
            401,
        )

    def test_access_token_requires_token_version_claim(self):
        token = create_access_token(
            self.user.id,
            self.user.role,
            self.user.token_version,
        )
        payload = decode_access_token(token)
        payload.pop("token_version")

        token_without_version = jwt.encode(
            payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM,
        )

        with self.assertRaises(HTTPException) as context:
            get_current_user(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=token_without_version,
                ),
                self.session,
            )

        self.assertEqual(
            context.exception.status_code,
            401,
        )

    def test_cookie_secure_defaults_to_true_without_environment_value(
        self,
    ):
        with self.temporary_cookie_secure(None):
            self.assertTrue(
                config.COOKIE_SECURE
            )

    def test_cookie_secure_configuration_supports_local_false_value(
        self,
    ):
        with self.temporary_cookie_secure("false"):
            self.assertFalse(
                config.COOKIE_SECURE
            )

    def test_refresh_cookie_uses_secure_configuration(self):
        for value, expected_secure in (
            ("true", True),
            ("false", False),
        ):
            with self.subTest(value=value):
                with self.temporary_cookie_secure(value):
                    response = Response()
                    auth_router.set_refresh_cookie(
                        response,
                        "test-refresh-token",
                    )

                    cookies = SimpleCookie()
                    cookies.load(response.headers["set-cookie"])
                    cookie = cookies["campusfix_refresh"]

                    self.assertEqual(
                        cookie["path"],
                        "/api/auth",
                    )
                    self.assertEqual(
                        cookie["samesite"],
                        "lax",
                    )
                    self.assertEqual(
                        cookie["max-age"],
                        "604800",
                    )
                    self.assertEqual(
                        cookie["httponly"],
                        True,
                    )
                    self.assertEqual(
                        bool(cookie["secure"]),
                        expected_secure,
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

    @patch(
        "app.auth.service.verify_password",
        return_value=True,
    )
    def test_banned_user_cannot_login(self, mock_verify):
        self.user.is_banned = True
        self.session.add(self.user)
        self.session.commit()

        with self.assertRaises(ValueError) as context:
            service.login(
                self.session,
                self.login_data(),
                "192.0.2.41",
            )

        self.assertEqual(
            str(context.exception),
            "Incorrect email or password.",
        )

        statement = select(LoginAttempt)
        attempts = self.session.exec(statement).all()

        self.assertEqual(len(attempts), 1)
        self.assertFalse(attempts[0].successful)

        refresh_sessions = self.session.exec(
            select(RefreshSession)
        ).all()
        self.assertEqual(len(refresh_sessions), 0)

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
            self.user.token_version,
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

    def test_banned_user_refresh_token_is_revoked(self):
        raw_token = "test-banned-refresh-token"
        sibling_token = "test-banned-sibling-token"
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
        sibling_record = RefreshSession(
            user_id=self.user.id,
            family_id=family_id,
            token_hash=hash_refresh_token(sibling_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

        self.session.add_all([
            refresh_record,
            sibling_record,
        ])

        self.user.is_banned = True
        self.session.add(self.user)
        self.session.commit()

        with self.assertRaises(ValueError):
            service.refresh_session(
                self.session,
                raw_token,
            )

        family_sessions = self.session.exec(
            select(RefreshSession).where(
                RefreshSession.family_id == family_id
            )
        ).all()

        self.assertEqual(len(family_sessions), 2)
        self.assertTrue(
            all(
                item.revoked_at is not None
                for item in family_sessions
            )
        )

    def test_self_service_session_revocation_is_scoped_to_user(self):
        other_user = User(
            id=uuid4(),
            email="other-student@test.com",
            name="Other Student",
            password_hash="test-hash",
            role="STUDENT",
            is_active=True,
        )
        family_id = uuid4()
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        target_sessions = [
            RefreshSession(
                user_id=self.user.id,
                family_id=family_id,
                token_hash=hash_refresh_token("target-session-token"),
                expires_at=expires_at,
            ),
            RefreshSession(
                user_id=self.user.id,
                family_id=family_id,
                token_hash=hash_refresh_token(
                    "target-session-rotated-token"
                ),
                expires_at=expires_at,
            ),
        ]
        other_user_session = RefreshSession(
            user_id=other_user.id,
            family_id=family_id,
            token_hash=hash_refresh_token("other-user-session-token"),
            expires_at=expires_at,
        )

        self.session.add_all([
            other_user,
            *target_sessions,
            other_user_session,
        ])
        self.session.commit()

        app = FastAPI()
        app.include_router(auth_router.router)

        def override_get_session():
            yield self.session

        app.dependency_overrides[get_session] = override_get_session
        token = create_access_token(
            self.user.id,
            self.user.role,
            self.user.token_version,
        )

        try:
            with TestClient(app) as client:
                response = client.delete(
                    f"/api/auth/sessions/{family_id}",
                    headers={
                        "Authorization": f"Bearer {token}"
                    },
                )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"message": "Session revoked successfully."},
        )

        for refresh_session in [
            *target_sessions,
            other_user_session,
        ]:
            self.session.refresh(refresh_session)

        self.assertTrue(
            all(
                item.revoked_at is not None
                for item in target_sessions
            )
        )
        self.assertIsNone(other_user_session.revoked_at)

    def test_logout_invalidates_access_token_and_only_current_family(self):
        raw_token = "logout-refresh-token"
        other_raw_token = "other-refresh-token"
        family_id = uuid4()
        other_family_id = uuid4()

        refresh_record = RefreshSession(
            user_id=self.user.id,
            family_id=family_id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )
        other_refresh_record = RefreshSession(
            user_id=self.user.id,
            family_id=other_family_id,
            token_hash=hash_refresh_token(other_raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

        self.session.add_all([
            refresh_record,
            other_refresh_record,
        ])
        self.session.commit()

        old_access_token = create_access_token(
            self.user.id,
            self.user.role,
            self.user.token_version,
        )

        service.logout(
            self.session,
            raw_token,
        )

        self.session.refresh(self.user)
        self.session.refresh(refresh_record)
        self.session.refresh(other_refresh_record)

        self.assertEqual(
            self.user.token_version,
            1,
        )
        self.assertIsNotNone(
            refresh_record.revoked_at
        )
        self.assertIsNone(
            other_refresh_record.revoked_at
        )

        with self.assertRaises(HTTPException):
            get_current_user(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=old_access_token,
                ),
                self.session,
            )

        refreshed = service.refresh_session(
            self.session,
            other_raw_token,
        )

        self.assertTrue(
            refreshed["response"].access_token
        )

    @patch(
        "app.auth.service.hash_password",
        return_value="new-password-hash",
    )
    @patch(
        "app.auth.service.verify_password",
        return_value=True,
    )
    def test_password_change_invalidates_access_and_all_families(
        self,
        mock_verify,
        mock_hash,
    ):
        first_raw_token = "first-password-refresh-token"
        second_raw_token = "second-password-refresh-token"
        first_family_id = uuid4()
        second_family_id = uuid4()

        first_record = RefreshSession(
            user_id=self.user.id,
            family_id=first_family_id,
            token_hash=hash_refresh_token(first_raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )
        second_record = RefreshSession(
            user_id=self.user.id,
            family_id=second_family_id,
            token_hash=hash_refresh_token(second_raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

        self.session.add_all([
            first_record,
            second_record,
        ])
        self.session.commit()

        old_access_token = create_access_token(
            self.user.id,
            self.user.role,
            self.user.token_version,
        )

        service.change_user_password(
            self.session,
            self.user,
            PasswordChangeRequest(
                current_password="OldPassword123",
                new_password="NewPassword123",
            ),
        )

        self.session.refresh(self.user)
        self.session.refresh(first_record)
        self.session.refresh(second_record)

        self.assertEqual(
            self.user.password_hash,
            "new-password-hash",
        )
        self.assertEqual(
            self.user.token_version,
            1,
        )
        self.assertIsNotNone(
            first_record.revoked_at
        )
        self.assertIsNotNone(
            second_record.revoked_at
        )

        with self.assertRaises(HTTPException):
            get_current_user(
                HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=old_access_token,
                ),
                self.session,
            )

        with self.assertRaises(ValueError):
            service.refresh_session(
                self.session,
                first_raw_token,
            )

    @patch(
        "app.auth.repository.revoke_refresh_family",
        side_effect=SQLAlchemyError("revocation failed"),
    )
    def test_logout_rolls_back_token_version_on_revocation_failure(
        self,
        mock_revoke,
    ):
        raw_token = "failed-logout-refresh-token"
        refresh_record = RefreshSession(
            user_id=self.user.id,
            family_id=uuid4(),
            token_hash=hash_refresh_token(raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

        self.session.add(refresh_record)
        self.session.commit()

        with self.assertRaises(SQLAlchemyError):
            service.logout(
                self.session,
                raw_token,
            )

        self.session.refresh(self.user)
        self.session.refresh(refresh_record)

        self.assertEqual(
            self.user.token_version,
            0,
        )
        self.assertIsNone(
            refresh_record.revoked_at
        )

    @patch(
        "app.auth.repository.revoke_user_refresh_sessions",
        side_effect=SQLAlchemyError("revocation failed"),
    )
    @patch(
        "app.auth.service.hash_password",
        return_value="new-password-hash",
    )
    @patch(
        "app.auth.service.verify_password",
        return_value=True,
    )
    def test_password_change_rolls_back_on_revocation_failure(
        self,
        mock_verify,
        mock_hash,
        mock_revoke,
    ):
        raw_token = "failed-password-refresh-token"
        refresh_record = RefreshSession(
            user_id=self.user.id,
            family_id=uuid4(),
            token_hash=hash_refresh_token(raw_token),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

        self.session.add(refresh_record)
        self.session.commit()
        original_password_hash = self.user.password_hash

        with self.assertRaises(SQLAlchemyError):
            service.change_user_password(
                self.session,
                self.user,
                PasswordChangeRequest(
                    current_password="OldPassword123",
                    new_password="NewPassword123",
                ),
            )

        self.session.refresh(self.user)
        self.session.refresh(refresh_record)

        self.assertEqual(
            self.user.password_hash,
            original_password_hash,
        )
        self.assertEqual(
            self.user.token_version,
            0,
        )
        self.assertIsNone(
            refresh_record.revoked_at
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
