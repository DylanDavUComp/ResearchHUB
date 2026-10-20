from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoginAttempt(Base):
    """Intento fallido de inicio de sesion, para limitar ataques de fuerza bruta.

    El correo se guarda como huella HMAC: no es reversible sin la clave secreta.
    """

    __tablename__ = "intentos_login"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    email_digest: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
