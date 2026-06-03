"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from backend.main import app


@pytest.fixture()
def client() -> TestClient:
    # `with` triggers the FastAPI lifespan (DB init, subsystem probes).
    with TestClient(app) as c:
        yield c
