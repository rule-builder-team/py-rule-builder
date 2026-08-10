from abc import ABC, abstractmethod
from typing import List

from domain.rule import Rule


class RuleRepository(ABC):

    @abstractmethod
    async def save(self, rule: Rule) -> Rule:
        pass

    @abstractmethod
    async def save_all(self, rules: List[Rule]) -> List[Rule]:
        pass

    @abstractmethod
    async def delete(self, ids: List[int]) -> List[Rule]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Rule]:
        pass

    @abstractmethod
    async def find_by_ids(self, ids: List[int]) -> List[Rule]:
        pass

    # ==========================================
    # התוספת החדשה - החוזה לבדיקת קיום חוק
    # ==========================================
    @abstractmethod
    async def check_exists(self, rule_type: str, value: str) -> bool:
        pass