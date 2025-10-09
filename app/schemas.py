from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Base schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "en"


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Telegram Mini App specific schemas
class TelegramUser(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    language: str = Field(..., min_length=2, max_length=10)
    native_language: str = Field(..., min_length=2, max_length=10)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class Course(CourseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order_index: int = Field(..., ge=1)


class LessonCreate(LessonBase):
    pass


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class Lesson(LessonBase):
    id: int
    course_id: int
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WordBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    translation: str = Field(..., min_length=1, max_length=500)
    pronunciation: Optional[str] = None
    example_sentence: Optional[str] = None
    difficulty_level: int = Field(1, ge=1, le=5)
    order_index: int = Field(..., ge=1)


class WordCreate(WordBase):
    pass


class WordUpdate(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=200)
    translation: Optional[str] = Field(None, min_length=1, max_length=500)
    pronunciation: Optional[str] = None
    example_sentence: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)


class Word(WordBase):
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
