import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.repository import Base
from dotenv import load_dotenv

load_dotenv()

# Настройка подключения к PostgreSQL из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/children_games"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency для получения сессии БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Инициализация БД - создание таблиц"""
    Base.metadata.create_all(bind=engine)

