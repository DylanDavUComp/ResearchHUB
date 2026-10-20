from pydantic import BaseModel, Field, field_validator

from app.modules.usuarios.models.user_application import ApplicationCode


def unique_applications(
    value: list[ApplicationCode] | None,
) -> list[ApplicationCode] | None:
    if value is None:
        return None
    return list(dict.fromkeys(value))


def default_applications() -> list[ApplicationCode]:
    return ["research_hub"]


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(min_length=1, max_length=80)
    status: str = Field(default="Activo", min_length=1, max_length=20)
    permissions: list[str] = Field(default_factory=list)


class UserCreate(UserBase):
    password: str = Field(min_length=12, max_length=128)
    applications: list[ApplicationCode] = Field(
        default_factory=default_applications,
        max_length=2,
    )

    _unique_applications = field_validator("applications")(unique_applications)


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=128)

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
    password: str | None = Field(default=None, min_length=12, max_length=128)
    # None conserva los accesos actuales.
    applications: list[ApplicationCode] | None = Field(default=None, max_length=2)

    _unique_applications = field_validator("applications")(unique_applications)


class UserRead(UserBase):
    id: str
    applications: list[ApplicationCode] = Field(default_factory=list)


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str
    # Aplicacion desde la que se inicia sesion; sin acceso no se emite token.
    application: ApplicationCode | None = None


class LoginResponse(BaseModel):
    # La sesion viaja en una cookie HttpOnly; el cuerpo nunca incluye credenciales.
    user: UserRead
