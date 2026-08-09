from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RuleRecord:
    type: str
    mode: str
    value: str
    active: bool = True


class RuleRepository(Protocol):
    def save(self, rule: RuleRecord) -> int:
        """Save an approved rule and return its database id."""
        ...