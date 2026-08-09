from sqlalchemy import MetaData, Table, insert
from sqlalchemy.engine import Engine

from src.application.ports.rule_repository import RuleRecord


class SqlAlchemyRuleRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

        metadata = MetaData()

        self._rules = Table(
            "rules",
            metadata,
            autoload_with=engine,
        )

    def save(self, rule: RuleRecord) -> int:
        statement = insert(self._rules).values(
            type=rule.type,
            mode=rule.mode,
            value=rule.value,
            active=rule.active,
        )

        with self._engine.begin() as connection:
            result = connection.execute(statement)

            return int(result.inserted_primary_key[0])