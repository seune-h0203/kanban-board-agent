"""DB connection and transactions; never auto-create tables on Supabase."""
import os
from contextlib import contextmanager
from collections.abc import Generator, Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def database_url() -> str:
    """Use an explicit database URL, otherwise a clearly isolated demo file."""
    return os.getenv("DATABASE_URL", "sqlite:///./kanban-demo.sqlite3")


def make_engine(url: str | None = None) -> Engine:
    """Build the engine. SQLite uses foreign keys; PostgreSQL uses a bounded pool."""
    url = url or database_url()
    options: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False, "timeout": 15}
    else:
        options.update(pool_size=5, max_overflow=5, pool_timeout=15)
    result = create_engine(url, **options)
    if result.dialect.name == "sqlite":
        @event.listens_for(result, "connect")
        def sqlite_fk(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return result


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Provide one disposable transaction per request."""
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


@contextmanager
def serialize_sqlite_write(db: Session) -> Iterator[None]:
    """Acquire the SQLite write lock before position lookup/mutation."""
    if db.bind and db.bind.dialect.name == "sqlite":
        # The session is not used for any reads before entry to this context.
        db.connection().exec_driver_sql("BEGIN IMMEDIATE")
    yield
