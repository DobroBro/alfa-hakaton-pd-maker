import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    from app.main import _service

    store = _service._store
    if hasattr(store, "_data"):
        store._data.clear()
    yield