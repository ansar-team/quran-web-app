from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    WordSchema, WordCreateSchema, WordUpdateSchema, SuccessResponseSchema
)
from app.crud import WordCRUD
# from app.api.dependencies import get_current_user
from app.utils.session_store import get_current_user

router = APIRouter(prefix="/words", tags=["words"])


@router.get("/lesson/{lesson_id}", response_model=List[WordSchema])
async def get_lesson_words(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all words for a specific lesson"""
    return WordCRUD.get_lesson_words(db, lesson_id, current_user.id)


@router.post("/lesson/{lesson_id}", response_model=WordSchema)
async def create_word(
        lesson_id: int,
        word_data: WordCreateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new word in a lesson"""
    # Verify lesson belongs to user
    from app.crud import LessonCRUD
    lesson = LessonCRUD.get_lesson(db, lesson_id, current_user.id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    return WordCRUD.create_word(db, word_data, lesson_id)


@router.get("/{word_id}", response_model=WordSchema)
async def get_word(
        word_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get a specific word"""
    word = WordCRUD.get_word(db, word_id, current_user.id)
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    return word


@router.put("/{word_id}", response_model=WordSchema)
async def update_word(
        word_id: int,
        word_data: WordUpdateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update a word"""
    word = WordCRUD.update_word(db, word_id, current_user.id, word_data)
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )
    return word


@router.delete("/{word_id}", response_model=SuccessResponseSchema)
async def delete_word(
        word_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Delete a word"""
    success = WordCRUD.delete_word(db, word_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )

    return SuccessResponseSchema(
        success=True,
        message="Word deleted successfully"
    )
