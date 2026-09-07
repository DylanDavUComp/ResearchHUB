from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.usuarios.models.role_permission import RolePermission


class Permission(Base):
    __tablename__ = "permisos"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    module: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
    )

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan",
    )
