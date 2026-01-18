from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.models import UserCreateRequest, User, GameScores, ScoreUpdateRequest
from app.repository import UserRepository
from app.database import get_db

router = APIRouter()


@router.get("/test")
async def root():
    return {"message": "Hello World"}


@router.get("/users", response_model=List[User])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db)
) -> List[User]:
    """Получить список всех пользователей с пагинацией"""
    user_repo = UserRepository(db)
    user_models = user_repo.get_all(skip=skip, limit=limit)
    
    # Преобразуем SQLAlchemy модели в Pydantic модели
    users = []
    for user_model in user_models:
        scores = GameScores(**user_model.scores)
        user = User(
            id=user_model.id,
            name=user_model.name,
            created_at=user_model.created_at,
            scores=scores
        )
        users.append(user)
    
    return users


@router.post("/users", response_model=User)
async def create_or_get_user(
    user_request: UserCreateRequest,
    db: Session = Depends(get_db)
) -> User:
    """Создать пользователя если его нет, или вернуть существующего"""
    user_repo = UserRepository(db)
    user_model = user_repo.create_or_get(user_request.id, user_request.name)
    
    # Преобразуем SQLAlchemy модель в Pydantic модель
    scores = GameScores(**user_model.scores)
    user = User(
        id=user_model.id,
        name=user_model.name,
        created_at=user_model.created_at,
        scores=scores
    )
    return user


@router.put("/users/{user_id}/scores/{game_name}", response_model=User)
async def update_game_score(
    user_id: UUID,
    game_name: str,
    score_request: ScoreUpdateRequest,
    db: Session = Depends(get_db)
) -> User:
    """Обновить очки для конкретной игры у пользователя"""
    valid_games = ["labyrinth", "treasure", "find_different"]
    
    if game_name not in valid_games:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимое имя игры. Доступные игры: {', '.join(valid_games)}"
        )
    
    user_repo = UserRepository(db)
    user_model = user_repo.update_scores(user_id, game_name, score_request.score)
    
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    
    # Преобразуем SQLAlchemy модель в Pydantic модель
    scores = GameScores(**user_model.scores)
    user = User(
        id=user_model.id,
        name=user_model.name,
        created_at=user_model.created_at,
        scores=scores
    )
    return user


@router.put("/users/{user_id}/scores", response_model=User)
async def update_all_scores(
    user_id: UUID,
    scores: GameScores,
    db: Session = Depends(get_db)
) -> User:
    """Обновить все очки игр у пользователя"""
    user_repo = UserRepository(db)
    scores_dict = scores.model_dump()
    user_model = user_repo.update(user_id, scores=scores_dict)
    
    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    
    # Преобразуем SQLAlchemy модель в Pydantic модель
    scores_obj = GameScores(**user_model.scores)
    user = User(
        id=user_model.id,
        name=user_model.name,
        created_at=user_model.created_at,
        scores=scores_obj
    )
    return user