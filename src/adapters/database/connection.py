from sqlalchemy import Engine, create_engine


def create_database_engine(database_url: str) -> Engine:
    """Create and return a SQLAlchemy engine for PostgreSQL."""

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )