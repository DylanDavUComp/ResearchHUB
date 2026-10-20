from pydantic import BaseModel

from app.modules.usuarios.schemas.user import UserRead


class WorkspaceSection(BaseModel):
    code: str
    name: str
    description: str
    available: bool


class WorkspaceRead(BaseModel):
    user: UserRead
    sections: list[WorkspaceSection]
