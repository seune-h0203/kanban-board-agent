"""Isolated real-SQLite API tests: no shared Supabase mutations."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event
from uuid import UUID

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.kanban import models
from app.kanban.seed import DEMO


@pytest.fixture
def env(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'test.db'}"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def fk(conn, _record):
        conn.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, expire_on_commit=False)
    ids = {k: UUID(v) for k, v in DEMO.items()}
    with maker() as db:
        db.add_all([
            models.User(id=ids["actor_id"], email="owner@example.test", name="Owner"),
            models.User(id=ids["editor_id"], email="editor@example.test", name="Editor"),
            models.User(id=ids["viewer_id"], email="viewer@example.test", name="Viewer"),
        ])
        db.flush()
        db.add(models.Board(id=ids["board_id"], owner_id=ids["actor_id"], name="test", description=None))
        db.flush()
        db.add_all([models.BoardMember(board_id=ids["board_id"], user_id=ids[key], role=role)
          for key,role in [("actor_id","owner"),("editor_id","editor"),("viewer_id","viewer")]])
        db.add_all([models.Column(id=ids[key], board_id=ids["board_id"], name=name, position=pos)
         for key,name,pos in [("todo_id","todo",1000),("doing_id","doing",2000),("done_id","done",3000)]])
        db.commit()
    def override():
        with maker() as db:
            yield db
    app.dependency_overrides[get_db] = override
    monkeypatch.setenv("TEAM_TODO_API_KEY", "pytest-only-token")
    try:
        with TestClient(app) as client:
            yield client, ids, maker, url
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def headers(env):
    _, ids, _, _ = env
    return {"X-Actor-ID": str(ids["actor_id"]), "X-API-Key": "pytest-only-token"}
