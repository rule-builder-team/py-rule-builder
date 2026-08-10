from typing import List
from sqlalchemy import delete, select, update, exists

from application.ports.outbound.rule_repository import RuleRepository
from database_service import database_service
from domain.rule import Rule, RuleMode, RuleType
from schema import RuleModel


class PostgresRuleRepository(RuleRepository):

    def __init__(self) -> None:
        self._db_service = database_service

    # ... פה נשארות שאר הפונקציות שלך: save, save_all, get_all, find_by_ids, delete ...

    # ==========================================
    # התוספת: מימוש הבדיקה מול מסד הנתונים
    # ==========================================
    async def check_exists(self, rule_type: str, value: str) -> bool:
        async with self._db_service.session_factory() as session:
            # מייצר שאילתת SELECT EXISTS מהירה
            stmt = select(exists().where(
                RuleModel.type == rule_type,
                RuleModel.value == str(value)
            ))
            result = await session.execute(stmt)
            return result.scalar()