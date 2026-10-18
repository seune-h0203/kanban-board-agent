"""API, SQLite relational integration, access control, and CLI mappings."""
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.kanban.models import Card, CardAssignee


def path(board, suffix=""):
    return f"/api/v1/boards/{board}{suffix}"


def test_all_discovery_endpoints(env, headers):
    client, ids, _, _ = env
    b = ids["board_id"]
    assert client.get("/health").json()["database"] == "not_checked"
    assert len(client.get("/api/v1/users", headers=headers).json()["items"]) == 3
    assert len(client.get("/api/v1/boards", headers=headers).json()["items"]) == 1
    assert client.get(path(b), headers=headers).json()["name"] == "test"
    assert len(client.get(path(b, "/members"), headers=headers).json()["items"]) == 3
    assert len(client.get(path(b, "/columns"), headers=headers).json()["items"]) == 3
    assert client.get(path(b, "/cards"), headers=headers).json()["items"] == []


def test_card_full_lifecycle_and_sqlite_persistence(env, headers):
    client, ids, maker, _ = env
    board = ids["board_id"]
    post = client.post(path(board,"/cards"),headers=headers,json={"title":"  create docs  ","column_id":str(ids["todo_id"]),"assignee_ids":[str(ids["editor_id"])]})
    assert post.status_code == 201, post.text
    card = post.json()
    assert card["title"] == "create docs" and card["position"] == 1000
    assert card["assignee_ids"] == [str(ids["editor_id"])]
    with maker() as db:
        assert db.scalar(select(Card).where(Card.id == UUID(card["id"]))) is not None
        assert db.scalar(select(CardAssignee).where(CardAssignee.card_id == UUID(card["id"]))) is not None
    assert client.get(f"/api/v1/cards/{card['id']}",headers=headers).json()["title"] == "create docs"
    assert len(client.get(path(board,"/cards"),headers=headers,params={"assignee_id":str(ids["editor_id"])}).json()["items"]) == 1
    change = client.patch(f"/api/v1/cards/{card['id']}",headers=headers,json={"title":"docs finished","column_id":str(ids["done_id"]),"assignee_ids":[],"due_date":"2026-10-20T09:00:00+09:00"})
    assert change.status_code == 200, change.text
    updated = change.json()
    assert updated["position"] == 1000 and updated["assignee_ids"] == []
    assert updated["due_date"].startswith("2026-10-20T00:00:00")
    assert len(client.get(path(board,"/cards"),headers=headers,params={"column_id":str(ids["done_id"])}).json()["items"]) == 1
    assert client.delete(f"/api/v1/cards/{card['id']}",headers=headers).status_code == 204
    assert client.get(f"/api/v1/cards/{card['id']}",headers=headers).status_code == 404
    with maker() as db:
        assert db.scalar(select(Card).where(Card.id == UUID(card["id"]))) is None


def test_missing_key_is_401(env, headers):
    client, ids, _, _ = env
    assert client.get("/api/v1/boards",headers={"X-Actor-ID":headers["X-Actor-ID"]}).status_code == 401
    assert client.get("/api/v1/boards").status_code == 422


def test_viewer_cannot_write_and_editor_can(env, headers):
    client, ids, _, _ = env
    viewer = {**headers, "X-Actor-ID":str(ids["viewer_id"])}
    editor = {**headers, "X-Actor-ID":str(ids["editor_id"])}
    body = {"title":"t", "column_id":str(ids["todo_id"])}
    assert client.post(path(ids["board_id"],"/cards"),headers=viewer,json=body).status_code == 403
    assert client.post(path(ids["board_id"],"/cards"),headers=editor,json=body).status_code == 201


def test_wrong_board_column_and_not_member_rejected(env, headers):
    client, ids, _, _ = env
    other = str(uuid4())
    assert client.get(path(other),headers=headers).status_code == 404
    data = {"title":"invalid","column_id":other}
    assert client.post(path(ids["board_id"],"/cards"),headers=headers,json=data).status_code == 422
    data["column_id"] = str(ids["todo_id"])
    data["assignee_ids"] = [other]
    assert client.post(path(ids["board_id"],"/cards"),headers=headers,json=data).status_code == 422
    invalid_actor = {**headers,"X-Actor-ID":other}
    assert client.get(path(ids["board_id"]),headers=invalid_actor).status_code == 403


@pytest.mark.parametrize("change", [{}, {"title":" "}, {"due_date":"2026-10-20"},{"column_id":None},{"assignee_ids":None}])
def test_invalid_patch_rejected(env,headers,change):
    client, ids, _, _ = env
    created=client.post(path(ids["board_id"],"/cards"),headers=headers,json={"title":"ok", "column_id":str(ids["todo_id"])}).json()
    response=client.patch(f"/api/v1/cards/{created['id']}",headers=headers,json=change)
    assert response.status_code == 422, response.text


def test_position_append_and_pagination(env,headers):
    client, ids, _, _=env
    for n in range(4):
        assert client.post(path(ids["board_id"],"/cards"),headers=headers,json={"title":f"t{n}","column_id":str(ids["todo_id"])}).status_code==201
    res=client.get(path(ids["board_id"],"/cards"),headers=headers,params={"limit":2,"offset":1}).json()
    assert [t["position"] for t in res["items"]]==[2000,3000]
    assert client.get(path(ids["board_id"],"/cards"),headers=headers,params={"limit":101}).status_code==422


def test_constraint_conflict_id(env,headers):
    client, ids, _, _=env
    task={"id":str(uuid4()),"title":"one","column_id":str(ids["todo_id"])}
    assert client.post(path(ids["board_id"],"/cards"),headers=headers,json=task).status_code==201
    assert client.post(path(ids["board_id"],"/cards"),headers=headers,json=task).status_code==409


def test_requires_key_configuration_in_default_mode(env,headers,monkeypatch):
    client, ids, _, _ = env
    monkeypatch.delenv("TEAM_TODO_API_KEY")
    monkeypatch.delenv("KANBAN_ALLOW_INSECURE_DEMO", raising=False)
    result=client.get("/api/v1/boards",headers=headers)
    assert result.status_code == 503
