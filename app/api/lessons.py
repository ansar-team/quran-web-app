from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    Lesson, LessonCreate, LessonUpdate, LessonWithWords,
    SuccessResponse
)
from app.crud import LessonCRUD, WordCRUD
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/course/{course_id}", response_model=List[Lesson])
async def get_course_lessons(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all lessons for a specific course"""
    return LessonCRUD.get_course_lessons(db, course_id, current_user.id)


@router.post("/course/{course_id}", response_model=Lesson)
async def create_lesson(
        lesson_data: LessonCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new lesson in a course"""
    # Verify course belongs to user
    from app.crud import CourseCRUD
    course = CourseCRUD.get_course(db, lesson_data.course_id, current_user.id)
    print(lesson_data)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return LessonCRUD.create_lesson(db, lesson_data)


@router.get("/{lesson_id}", response_model=LessonWithWords)
async def get_lesson(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get a specific lesson with words"""
    lesson = LessonCRUD.get_lesson(db, lesson_id, current_user.id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    words = WordCRUD.get_lesson_words(db, lesson_id, current_user.id)

    return LessonWithWords(
        **lesson.__dict__,
        words=words
    )


@router.put("/{lesson_id}", response_model=Lesson)
async def update_lesson(
        lesson_id: int,
        lesson_data: LessonUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update a lesson"""
    lesson = LessonCRUD.update_lesson(db, lesson_id, current_user.id, lesson_data)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    return lesson


@router.delete("/{lesson_id}", response_model=SuccessResponse)
async def delete_lesson(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Delete a lesson"""
    success = LessonCRUD.delete_lesson(db, lesson_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )

    return SuccessResponse(
        success=True,
        message="Lesson deleted successfully"
    )
