from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    CourseSchema, CourseCreateSchema, CourseUpdateSchema, CourseWithLessonsAndWordsSchema,
    SuccessResponseSchema
)
from app.crud import CourseCRUD
from app.api.dependencies import get_current_user


router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=List[CourseSchema])
async def get_user_courses(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all courses for the current user"""
    return CourseCRUD.get_user_courses(db, current_user.id)


@router.post("/", response_model=CourseSchema)
async def create_course(
        course_data: CourseCreateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new course"""
    return CourseCRUD.create_course(db, course_data, current_user.id)


@router.get("/{course_id}", response_model=CourseWithLessonsAndWordsSchema)
async def get_course(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get a specific course with lessons and words"""
    course = CourseCRUD.get_course(db, course_id, current_user.id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Load lessons with words
    from app.crud import LessonCRUD, WordCRUD
    from app.schemas import LessonWithWordsSchema

    lessons = LessonCRUD.get_course_lessons(db, course_id, current_user.id)

    # course_with_lessons = CourseWithLessonsAndWords(
    #     **course.__dict__,
    #     lessons=[]
    # )
    lessons_with_words = []
    for lesson in lessons:
        words = WordCRUD.get_lesson_words(db, lesson.id, current_user.id)
        lesson_with_words = LessonWithWordsSchema(
            **lesson.__dict__,
            words=words
        )
        lessons_with_words.append(lesson_with_words)
        # course_with_lessons.lessons.append(lesson_with_words)

    # return course_with_lessons
    return CourseWithLessonsAndWordsSchema(
        **course.__dict__,
        lessons=lessons_with_words
    )

@router.put("/{course_id}", response_model=CourseSchema)
async def update_course(
        course_id: int,
        course_data: CourseUpdateSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update a course"""
    course = CourseCRUD.update_course(db, course_id, current_user.id, course_data)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course


@router.delete("/{course_id}", response_model=SuccessResponseSchema)
async def delete_course(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Delete a course"""
    success = CourseCRUD.delete_course(db, course_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return SuccessResponseSchema(
        success=True,
        message="Course deleted successfully"
    )
