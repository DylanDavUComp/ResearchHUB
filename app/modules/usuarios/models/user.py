from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.usuarios.models.user_role import UserRole


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    # LEGACY:
    # Se mantiene durante la migración.
    role: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Activo",
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # LEGACY:
    # Se mantiene durante la migración.
    permissions: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    roles = relationship(
        "Role",
        secondary="usuario_roles",
        back_populates="users",
        viewonly=True,
    )
