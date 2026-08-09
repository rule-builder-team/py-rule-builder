from sqlalchemy import create_engine, text

from src.adapters.database.rule_repository import SqlAlchemyRuleRepository
from src.application.ports.rule_repository import RuleRecord


def test_save_rule() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type VARCHAR(20) NOT NULL,
                    mode VARCHAR(20) NOT NULL,
                    value VARCHAR(255) NOT NULL,
                    active BOOLEAN NOT NULL DEFAULT 1
                )
                """
            )
        )

    repository = SqlAlchemyRuleRepository(engine)

    rule_id = repository.save(
        RuleRecord(
            type="ip",
            mode="blacklist",
            value="192.168.1.10",
        )
    )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, type, mode, value, active
                FROM rules
                WHERE id = :id
                """
            ),
            {"id": rule_id},
        ).mappings().one()

    assert row["type"] == "ip"
    assert row["mode"] == "blacklist"
    assert row["value"] == "192.168.1.10"
    assert bool(row["active"]) is True