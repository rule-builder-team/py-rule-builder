from sqlalchemy import Boolean, Integer, String, UniqueConstraint, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# מייבאים את ה-Enum של הדומיין כדי לקשור אותו ל-DB
from domain.rule import RuleType
from config import config


class Base(DeclarativeBase):
    pass


class RuleModel(Base):
    __tablename__ = "firewall_rules"  # שים לב שאמרנו שצריך לתקן את ההפניה ל-config

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # שינוי 1: סוג החוק מוגבל ל-IP, DOMAIN, או PORT לפי הדומיין
    type: Mapped[RuleType] = mapped_column(Enum(RuleType, name="rule_type_enum"), nullable=False)

    # שינוי 2: המוד מוגבל ל-blacklist או whitelist בלבד ברמת ה-DB
    mode: Mapped[str] = mapped_column(Enum("blacklist", "whitelist", name="rule_mode_enum"), nullable=False)

    value: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('type', 'value', name='uix_type_value'),
    )