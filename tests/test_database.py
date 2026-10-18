"""Physical schema foreign keys and read-only inspector integration."""
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from app.kanban.inspect_database import inspect_board_database
from app.kanban.models import Card


def test_schema_and_existing_data_read_only(env):
    _,ids,_,url=env
    report=inspect_board_database(url)
    assert report["required_columns_present"]
    assert len(report["tables"])==6
    assert report["mode"]=="read-only"
    assert len(report["boards"])==1
    assert len(report["columns"])==3
    assert inspect_database_fk(report)


def inspect_database_fk(report):
    return any(x["referred_table"] == "columns" for x in report["tables"]["cards"]["foreign_keys"])


def test_sqlite_fk_enforced(env):
    _,ids,maker,_=env
    try:
        with maker() as db:
            db.add(Card(title="Orphan",column_id=UUID("00000000-0000-0000-0000-000000000001"),position=1000,created_by=ids["actor_id"]))
            try:
                db.commit()
            except (IntegrityError, ValueError):
                return
    except (IntegrityError, ValueError):
        return
    raise AssertionError("Foreign keys must reject orphan cards")
