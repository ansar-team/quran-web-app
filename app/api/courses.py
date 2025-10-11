from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    Course, CourseCreate, CourseUpdate, CourseWithLessonsAndWords,
    SuccessResponse
)
from app.crud import CourseCRUD
from app.api.dependencies import get_current_user
import os

router = APIRouter(prefix="/courses", tags=["courses"])

# Configure templates relative to this file
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "../templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/", response_class=HTMLResponse)
async def get_user_courses(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    courses_list = CourseCRUD.get_user_courses(db, current_user.id)
    return templates.TemplateResponse("courses.html", {
        "request": request,
        "courses": courses_list
    })

@router.post("/", response_model=Course)
async def create_course(
        course_data: CourseCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new course"""
    return CourseCRUD.create_course(db, course_data, current_user.id)


@router.get("/{course_id}", response_model=CourseWithLessonsAndWords)
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
    lessons = LessonCRUD.get_course_lessons(db, course_id, current_user.id)

    course_with_lessons = CourseWithLessonsAndWords(
        **course.__dict__,
        lessons=[]
    )

    for lesson in lessons:
        words = WordCRUD.get_lesson_words(db, lesson.id, current_user.id)
        lesson_with_words = {
            **lesson.__dict__,
            "words": words
        }
        course_with_lessons.lessons.append(lesson_with_words)

    return course_with_lessons


@router.put("/{course_id}", response_model=Course)
async def update_course(
        course_id: int,
        course_data: CourseUpdate,
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


@router.delete("/{course_id}", response_model=SuccessResponse)
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

    return SuccessResponse(
        success=True,
        message="Course deleted successfully"
    )
