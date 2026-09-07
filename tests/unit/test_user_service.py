from unittest.mock import Mock

from app.modules.usuarios.services.user_service import UserService


def test_seed_users_adds_superadmin_when_other_users_exist(monkeypatch) -> None:
    repository = Mock()
    repository.get_by_email.side_effect = [None, object(), object()]

    service = UserService.__new__(UserService)
    service.repository = repository

    created_emails = []

    def create_user(payload):
        created_emails.append(payload.email)

    monkeypatch.setattr(service, "create", create_user)

    service.ensure_seed_users()

    assert "superadmin@researchhub-u.edu.co" in created_emails
