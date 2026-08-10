import asyncio
from option import Result, Ok, Err
from application_error import ApplicationError
from domain.rule import Rule, RuleType
from application.ports.outbound.rule_repository import RuleRepository
from your_validation_file import ApplicationError


from src.adapters.queue.consumer import AddRuleMessage, DeleteRuleMessage, UpdateStatusMessage


class FirewallService:

    def __init__(self, rule_repository: RuleRepository) -> None:
        self.rule_repository = rule_repository

    async def add_rules(self, command: AddRuleMessage) -> Result[None, ApplicationError]:
        rule_type = command.rule_type
        mode = command.mode

        tasks = []
        for value in command.values:
            # 1. בדיקה מול בסיס הנתונים (כבר היה לנו)
            existing_rule = await self.rule_repository.find_by_type_and_value(rule_type, value)

            if existing_rule:
                if existing_rule.mode != mode:
                    return Err(ApplicationError(
                        code="RULE_CONFLICT",
                        message=f"Cannot add '{value}' to {mode}. It already exists in {existing_rule.mode}."
                    ))
                else:
                    return Err(ApplicationError(
                        code="RULE_ALREADY_EXISTS",
                        message=f"Rule '{value}' already exists in {mode}."
                    ))

            # ==========================================
            # 2. התיקון: שימוש ב-Factory Method של ה-Domain
            # ==========================================
            rule_creation_result = Rule.create(
                rule_type=rule_type,
                mode=mode,
                value=value,
                active=True
            )

            # אם הישות סירבה להיווצר בגלל חוקים עסקיים של הדומיין (כמו IP פגום)
            if rule_creation_result.is_err:
                domain_err = rule_creation_result.unwrap_err()
                # ממירים את שגיאת הדומיין לשגיאת אפליקציה מובנית
                return Err(ApplicationError(
                    code=domain_err.code,
                    message=domain_err.message
                ))

            # שולפים את הישות מתוך ה-Ok
            new_rule = rule_creation_result.unwrap()

            tasks.append(self.rule_repository.save(new_rule))

        await asyncio.gather(*tasks)
        return Ok(None)


    async def delete_rules(self, command: DeleteRuleMessage) -> Result[None, ApplicationError]:
        ids = command.ids

        existing = await self.rule_repository.find_by_ids(ids)
        if len(existing) != len(ids):
            return Err(ApplicationError(
                code="RULE_NOT_FOUND",
                message="Cannot delete. Some rules were not found in the database."
            ))

        await self.rule_repository.delete(ids)
        return Ok(None)


    async def update_rules_status(self, command: UpdateStatusMessage) -> Result[None, ApplicationError]:
        ids = command.ids
        active = command.active

        existing_rules = await self.rule_repository.find_by_ids(ids)
        if len(existing_rules) != len(ids):
            return Err(ApplicationError(
                code="RULE_NOT_FOUND",
                message="Cannot update status. Some rules were not found."
            ))

        for rule in existing_rules:
            rule.update_status(active)

        await self.rule_repository.save_all(existing_rules)
        return Ok(None)