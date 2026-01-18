from uuid import UUID, uuid4
from datetime import datetime

from pydantic import BaseModel, Field

class GameScores(BaseModel):
    labyrinth: int = 0
    treasure: int = 0
    find_different: int = 0

class User(BaseModel):
    id: UUID
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    scores: GameScores = Field(default_factory=GameScores)

class UserCreateRequest(BaseModel):
    """Модель для запроса на создание/получение пользователя"""
    id: UUID
    name: str

class ScoreUpdateRequest(BaseModel):
    """Модель для запроса на обновление очков одной игры"""
    score: int = Field(ge=0, description="Новое значение очков (не может быть отрицательным)")
