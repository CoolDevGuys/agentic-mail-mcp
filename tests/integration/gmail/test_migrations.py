from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _alembic_config(db_url: str) -> Config:
    cfg = Config(str(_REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_REPO_ROOT / "migrations"))
    # env.py reads this injected url instead of Settings.
    cfg.attributes["sqlalchemy.url"] = db_url
    return cfg


def test_upgrade_creates_schema(tmp_path: Path) -> None:
    db_file = tmp_path / "migrate.db"
    url = f"sqlite:///{db_file}"

    command.upgrade(_alembic_config(url), "head")

    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert {"emails", "threads", "attachments", "labels"} <= tables


def test_downgrade_removes_schema(tmp_path: Path) -> None:
    db_file = tmp_path / "migrate2.db"
    url = f"sqlite:///{db_file}"
    cfg = _alembic_config(url)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(url)
    tables = set(inspect(engine).get_table_names())
    assert not ({"emails", "threads", "attachments", "labels"} & tables)
