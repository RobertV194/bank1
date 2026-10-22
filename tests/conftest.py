"""Спільні фікстури: ізольований застосунок із БД у пам'яті та окремими структурами."""
import pytest

from web_app.app import create_app


@pytest.fixture
def app():
    return create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })


@pytest.fixture
def client(app):
    return app.test_client()