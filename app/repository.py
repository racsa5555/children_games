from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from abc import ABC, abstractmethod

from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, attributes
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

Base = declarative_base()


# SQLAlchemy модели
class UserModel(Base):
    __tablename__ = "users"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    scores = Column(JSON, nullable=False, default={
        "labyrinth": 0,
        "treasure": 0,
        "find_different": 0
    })


# Базовый интерфейс репозитория
class BaseRepository(ABC):
    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def create(self, **kwargs):
        pass

    @abstractmethod
    def get_by_id(self, id: UUID):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def update(self, id: UUID, **kwargs):
        pass

    @abstractmethod
    def delete(self, id: UUID):
        pass


# Репозиторий для работы с пользователями
class UserRepository(BaseRepository):
    def create(self, name: str, user_id: Optional[UUID] = None, scores: Optional[dict] = None) -> UserModel:
        """Создать нового пользователя"""
        if scores is None:
            scores = {"labyrinth": 0, "treasure": 0, "find_different": 0}
        
        user = UserModel(
            id=user_id if user_id else uuid4(),
            name=name,
            created_at=datetime.now(),
            scores=scores
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def create_or_get(self, user_id: UUID, name: str) -> UserModel:
        """Создать пользователя если его нет, или вернуть существующего"""
        user = self.get_by_id(user_id)
        if user:
            return user
        
        # Создаем нового пользователя с указанным ID
        return self.create(name=name, user_id=user_id)

    def get_by_id(self, id: UUID) -> Optional[UserModel]:
        """Получить пользователя по ID"""
        return self.session.query(UserModel).filter(UserModel.id == id).first()

    def get_by_name(self, name: str) -> Optional[UserModel]:
        """Получить пользователя по имени"""
        return self.session.query(UserModel).filter(UserModel.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Получить всех пользователей с пагинацией"""
        return self.session.query(UserModel).offset(skip).limit(limit).all()

    def update(self, id: UUID, name: Optional[str] = None, 
               scores: Optional[dict] = None) -> Optional[UserModel]:
        """Обновить данные пользователя"""
        user = self.get_by_id(id)
        if not user:
            return None
        
        if name is not None:
            user.name = name
        if scores is not None:
            user.scores = scores
        
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_scores(self, id: UUID, game: str, score: int) -> Optional[UserModel]:
        """Обновить очки для конкретной игры"""
        user = self.get_by_id(id)
        if not user:
            return None
        
        if user.scores is None:
            user.scores = {}
        
        # Обновляем значение в словаре
        user.scores[game] = score
        # Явно помечаем поле как измененное для SQLAlchemy
        # Это необходимо, так как SQLAlchemy не отслеживает изменения внутри JSON полей
        attributes.flag_modified(user, "scores")
        
        self.session.commit()
        self.session.refresh(user)
        return user

    def delete(self, id: UUID) -> bool:
        """Удалить пользователя"""
        user = self.get_by_id(id)
        if not user:
            return False
        
        self.session.delete(user)
        self.session.commit()
        return True


# Класс для управления репозиториями
class Repository:
    def __init__(self, session: Session):
        self.session = session
        self.users = UserRepository(session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

