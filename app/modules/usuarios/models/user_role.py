from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.usuarios.models.role import Role
    from app.modules.usuarios.models.user import User


class UserRole(Base):
    __tablename__ = "usuario_roles"

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="user_roles",
    )

    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_roles",
    )
