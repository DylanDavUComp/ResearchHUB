from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(min_length=1, max_length=80)
    status: str = Field(default="Activo", min_length=1, max_length=20)
    permissions: list[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_institutional_email(cls, value: str) -> str:
        email = value.strip().lower()

        if not email.endswith("@ucompensar.edu.co"):
            raise ValueError(
                "Solo se permiten correos institucionales @ucompensar.edu.co."
            )

        return email


class UserUpdate(UserBase):
    password: str | None = Field(default=None, min_length=8)


class UserRead(UserBase):
    id: str


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
