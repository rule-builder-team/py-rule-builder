from sqlalchemy import Engine

from src.adapters.database.connection import create_database_engine


def test_create_database_engine() -> None:
    database_url = (
        "postgresql+psycopg://"
        "test_user:test_password@localhost:5432/test_database"
    )

    engine = create_database_engine(database_url)

    assert isinstance(engine, Engine)
    assert engine.url.drivername == "postgresql+psycopg"
    assert engine.url.host == "localhost"
    assert engine.url.port == 5432
    assert engine.url.database == "test_database"

    engine.dispose()