import os

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY_TOKEN"] = "test-secret-key-not-for-production"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["INITIAL_ADMIN_USERNAME"] = "admin_pruebas"
os.environ["INITIAL_ADMIN_PASSWORD"] = "AdminPruebas123"
os.environ["INITIAL_ADMIN_NOMBRE"] = "Admin"
os.environ["INITIAL_ADMIN_APELLIDO"] = "Pruebas"
os.environ["INITIAL_ADMIN_EMAIL"] = "admin.pruebas@example.com"

from database import engine
from main import app


@pytest.fixture
def client():
    SQLModel.metadata.drop_all(engine)
    with TestClient(app) as test_client:
        yield test_client
    SQLModel.metadata.drop_all(engine)
