
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name", "email")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    email: EmailStr | None = None
    current_password: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None:
            value = value.strip()

            if len(value) < 2:
                raise ValueError(
                    "Name must contain at least 2 characters."
                )

        return value

    @field_validator("email")
    @classmethod
    def normalize_email(
        cls,
        value: EmailStr | None,
    ) -> EmailStr | None:
        if value is not None:
            return value.strip().lower()

        return value

    @model_validator(mode="after")
    def validate_profile_update(self):
        if self.name is None and self.email is None:
            raise ValueError(
                "Provide at least one profile field to update."
            )

        if self.email is not None and self.current_password is None:
            raise ValueError(
                "Current password is required to change email."
            )

        return self


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )
    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @model_validator(mode="after")
    def validate_new_password(self):
        if self.current_password == self.new_password:
            raise ValueError(
                "New password must be different from the current password."
            )

        return self


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
