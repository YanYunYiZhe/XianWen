"""Shared pytest fixtures for Web/API tests.

Tests must not call real model services. Use this module's client factory and
keep AI behind Mock/fallback paths when that layer lands.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from xianwen.main import app as default_app


def create_app() -> FastAPI:
    """Return the shared FastAPI application used by Web tests."""
    return default_app


def create_test_client(application: FastAPI | None = None) -> TestClient:
    """Create a client bound to the given app (or the shared default app)."""
    return TestClient(application or create_app())


@pytest.fixture
def app() -> FastAPI:
    """Application fixture used by Web and smoke tests."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """HTTP client fixture; prefers context-managed lifecycle over globals."""
    with create_test_client(app) as test_client:
        yield test_client
