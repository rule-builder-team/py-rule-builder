import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

# ייבוא אובייקט הקונפיגורציה וה-Logger
from config import config
from logger import logger


class DatabaseService:
    _instance: Optional["DatabaseService"] = None

    def __init__(self) -> None:
        self.engine: Optional[AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @classmethod
    def get_instance(cls) -> "DatabaseService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect_with_retry(self, max_retries: int = 5) -> None:
        """
        Creates an asynchronous database engine and attempts to connect
        with exponential backoff retries.
        """
        # 1. הפיכת ה-database_uri של PostgreSQL לפורמט אסינכרוני (postgresql+asyncpg://)
        db_url = config.database_uri
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # 2. יצירת ה-AsyncEngine של SQLAlchemy (מקביל ל-Pool)
        self.engine = create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,  # בודק תקינות חיבור לפני שימוש
        )

        # 3. יצירת Session Factory לניהול שאילתות אסינכרוניות
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        attempt = 1
        # אם קיימת הגדרת אינטרוואל בקונפיגורציה נשתמש בה, אחרת ברירת מחדל של 1000 מ"ש
        initial_interval_ms = getattr(config, "db_connection_interval", 1000)
        current_interval_seconds = initial_interval_ms / 1000.0

        while attempt <= max_retries:
            try:
                # ביצוע שאילתת בדיקה (SELECT 1)
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))

                logger.info(
                    "database_connected_successfully",
                    attempt=attempt,
                    env=config.env,
                )
                return

            except Exception as exc:
                logger.error(
                    "database_connection_failed",
                    attempt=attempt,
                    max_retries=max_retries,
                    error=str(exc),
                )

                if attempt == max_retries:
                    logger.critical("database_max_retries_reached_halting")
                    # עצירת האפליקציה בדומה ל-process.exit(1)
                    raise SystemExit(1)

                logger.info(
                    "database_waiting_for_retry",
                    wait_seconds=current_interval_seconds,
                )
                await asyncio.sleep(current_interval_seconds)

                # Exponential Backoff (הכפלת הניסיון הבא)
                current_interval_seconds *= 2
                attempt += 1

    async def close(self) -> None:
        """סגירת ה-Pool בצורה נקייה בזמן כיבוי השרת."""
        if self.engine:
            await self.engine.dispose()
            logger.info("database_connection_closed")


# ייצוא אובייקט הסינגלטון (מקביל ל-export const databaseService)
database_service = DatabaseService.get_instance()