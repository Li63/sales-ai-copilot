from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, inspect

from app.core import init_db


def test_ensure_persona_source_columns_adds_source_url(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table(
        "persona_sources",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("source_type", String(32), nullable=False),
    )
    metadata.create_all(engine)
    monkeypatch.setattr(init_db, "engine", engine)

    init_db._ensure_persona_source_columns()

    columns = {column["name"] for column in inspect(engine).get_columns("persona_sources")}
    assert "source_url" in columns
