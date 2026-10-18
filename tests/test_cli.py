"""Invoke Typer commands against the real API TestClient, no external server."""
import json
from typer.testing import CliRunner
import app.cli as cli

runner = CliRunner()


def invoke(monkeypatch, client, ids, *args):
    monkeypatch.setattr(cli,"_make_client",lambda url:client)
    return runner.invoke(cli.app,["--actor-id",str(ids["actor_id"]),"--api-key","pytest-only-token",*args])


def test_cli_all_read_commands_and_formats(env,monkeypatch):
    client,ids,_,_=env
    for cmd in [["health"],["kanban","users"],["kanban","boards"],["kanban","board",str(ids["board_id"])],["kanban","members",str(ids["board_id"])],["kanban","columns",str(ids["board_id"])],["kanban","list",str(ids["board_id"])]]:
        result=invoke(monkeypatch,client,ids,*cmd)
        assert result.exit_code==0,(cmd,result.output,result.exception)
    r=invoke(monkeypatch,client,ids,"--json","kanban","boards")
    assert r.exit_code==0,r.output
    assert json.loads(r.output)["items"][0]["id"] == str(ids["board_id"])
    r=invoke(monkeypatch,client,ids,"--text","kanban","boards")
    assert "Name: test" in r.output


def test_cli_create_get_update_delete_with_json(env,monkeypatch):
    client,ids,_,_=env
    res=invoke(monkeypatch,client,ids,"--json","kanban","create",str(ids["board_id"]),"--column-id",str(ids["todo_id"]),"--title","cli card","--assignee-id",str(ids["editor_id"]))
    assert res.exit_code==0,(res.output,res.exception)
    card=json.loads(res.output)
    get=invoke(monkeypatch,client,ids,"--json","kanban","get",card["id"])
    assert json.loads(get.output)["title"] == "cli card"
    update=invoke(monkeypatch,client,ids,"--json","kanban","update",card["id"],"--column-id",str(ids["done_id"]),"--clear-assignees")
    assert update.exit_code==0,update.output
    assert json.loads(update.output)["assignee_ids"]==[]
    delete=invoke(monkeypatch,client,ids,"--json","kanban","delete",card["id"])
    assert delete.exit_code==0,delete.output
    assert json.loads(delete.output)=={"deleted":True}


def test_cli_codex_register_idempotent_and_move(env,monkeypatch):
    client,ids,_,_=env
    common=["kanban","register",str(ids["board_id"]),"--work-key","assignment7/backend","--title","Build backend"]
    created=invoke(monkeypatch,client,ids,"--json",*common,"--column-id",str(ids["todo_id"]))
    assert created.exit_code==0,(created.output,created.exception)
    card=json.loads(created.output)
    moved=invoke(monkeypatch,client,ids,"--json",*common,"--column-id",str(ids["done_id"]),"--description","Tests passed")
    assert moved.exit_code==0,(moved.output,moved.exception)
    changed=json.loads(moved.output)
    assert changed["id"]==card["id"] and changed["column_id"]==str(ids["done_id"])
    items=invoke(monkeypatch,client,ids,"--json","kanban","list",str(ids["board_id"]))
    assert len(json.loads(items.output)["items"])==1


def test_cli_invalid_actor_is_clean_error(env,monkeypatch):
    client,ids,_,_=env
    res=runner.invoke(cli.app,["kanban","boards"])
    assert res.exit_code!=0
    assert "actor-id" in res.output


def test_cli_http_error_json(env,monkeypatch):
    client,ids,_,_=env
    r=invoke(monkeypatch,client,ids,"--json","kanban","get","3df02b12-7994-4a58-bf5c-6441bb365df6")
    assert r.exit_code==1
    assert json.loads(r.output)["error"]["status"]==404


def test_cli_empty_work_key_fails_before_remote_save(env,monkeypatch):
    client, ids, _, _ = env
    result=invoke(monkeypatch,client,ids,"--json","kanban","register",str(ids["board_id"]),"--column-id",str(ids["todo_id"]),"--work-key","  ","--title","empty")
    assert result.exit_code != 0
    assert "nonempty" in result.output
