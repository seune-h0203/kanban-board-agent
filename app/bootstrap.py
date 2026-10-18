"""Explicit demo initializer; refuses external databases."""
import json
from app.db.base import Base
from app.db.session import engine
from app.kanban import models  # noqa: F401 (register models)
from app.kanban.seed import seed_demo


def main() -> None:
    """Create a local SQLite-only demo database and seeded test board."""
    if engine.dialect.name != "sqlite":
        raise SystemExit("Refusing to initialize a shared database. Provide existing tables manually.")
    Base.metadata.create_all(engine)
    print(json.dumps(seed_demo(), indent=2))


if __name__ == "__main__":
    main()
