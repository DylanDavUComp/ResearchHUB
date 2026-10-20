from collections.abc import Iterator

import pytest
from app.core.telemetry import CSRF_HEADER, CSRF_HEADER_VALUE
from app.main import app
from fastapi.testclient import TestClient

APP_HEADERS = {CSRF_HEADER: CSRF_HEADER_VALUE}


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, headers=APP_HEADERS) as test_client:
        yield test_client
