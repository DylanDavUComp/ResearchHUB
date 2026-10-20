from collections.abc import Generator

import pytest
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.telemetry import CSRF_HEADER, CSRF_HEADER_VALUE
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def auth_client(
    session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """Cliente real de punta a punta: login, cookie de sesion y PostgreSQL simulado.

    El cliente de pruebas usa http://testserver, donde el navegador no enviaria una
    cookie Secure; por eso se desactiva solo aqui.
    """

    def override_db() -> Generator[Session, None, None]:
        with session_factory() as db:
            yield db

    monkeypatch.setattr(settings, "session_cookie_secure", False)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app, headers={CSRF_HEADER: CSRF_HEADER_VALUE}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
