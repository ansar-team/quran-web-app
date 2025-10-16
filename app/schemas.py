from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from enum import IntEnum


class RatingEnum(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class StateEnum(IntEnum):
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


# Base schemas
class UserBaseSchema(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: str = "en"


class UserCreateSchema(UserBaseSchema):
    pass


class UserSchema(UserBaseSchema):
    id: int
    current_streak: int = 0
    longest_streak: int = 0
    last_active_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Telegram Mini App specific schemas
class TelegramUserSchema(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class CourseBaseSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    language: str = Field(..., min_length=2, max_length=10)
    native_language: str = Field(..., min_length=2, max_length=10)


class CourseCreateSchema(CourseBaseSchema):
    pass


class CourseUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class CourseSchema(CourseBaseSchema):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LessonBaseSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    order_index: int = Field(..., ge=1)


class LessonCreateSchema(LessonBaseSchema):
    course_id: int


class LessonUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class LessonSchema(LessonBaseSchema):
    id: int
    course_id: int
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WordBaseSchema(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    translation: str = Field(..., min_length=1, max_length=500)
    pronunciation: Optional[str] = None
    example_sentence: Optional[str] = None
    difficulty_level: int = Field(1, ge=1, le=5)
    order_index: int = Field(..., ge=1)


class WordCreateSchema(WordBaseSchema):
    pass


class WordUpdateSchema(BaseModel):
    text: Optional[str] = Field(None, min_length=1, max_length=200)
    translation: Optional[str] = Field(None, min_length=1, max_length=500)
    pronunciation: Optional[str] = None
    example_sentence: Optional[str] = None
    difficulty_level: Optional[int] = Field(None, ge=1, le=5)


class WordSchema(WordBaseSchema):
    id: int
    lesson_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWordBaseSchema(BaseModel):
    word_id: int
    fsrs_card_data: Dict[str, Any]


class UserWordCreateSchema(UserWordBaseSchema):
    pass


class UserWordUpdateSchema(BaseModel):
    fsrs_card_data: Optional[Dict[str, Any]] = None


class UserWordSchema(UserWordBaseSchema):
    id: int
    user_id: int
    total_reviews: int
    correct_reviews: int
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewBaseSchema(BaseModel):
    rating: RatingEnum
    response_time_seconds: Optional[float] = None
    lesson_context: Optional[int] = None


class ReviewCreateSchema(ReviewBaseSchema):
    pass


class ReviewSchema(ReviewBaseSchema):
    id: int
    user_word_id: int
    review_datetime: datetime
    scheduled_days: Optional[int] = None
    elapsed_days: Optional[int] = None
    review: Optional[int] = None
    lapses: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LessonProgressBaseSchema(BaseModel):
    lesson_id: int
    words_learned: int = 0
    words_to_review: int = 0
    total_words: int


class LessonProgressCreateSchema(LessonProgressBaseSchema):
    is_started: Optional[bool] = None
    is_completed: Optional[bool] = None


class LessonProgressUpdateSchema(BaseModel):
    words_learned: Optional[int] = None
    words_to_review: Optional[int] = None
    total_words: Optional[int] = None
    is_started: Optional[bool] = None
    is_completed: Optional[bool] = None


class LessonProgressSchema(LessonProgressBaseSchema):
    id: int
    user_id: int
    is_started: bool
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Complex schemas for API responses
class LessonWithWordsSchema(LessonSchema):
    words: List[WordSchema] = []


class CourseWithLessonsSchema(CourseSchema):
    lessons: List[LessonSchema] = []


class CourseWithLessonsAndWordsSchema(CourseSchema):
    lessons: List[LessonWithWordsSchema] = []


class WordWithProgressSchema(WordSchema):
    user_word: Optional[UserWordSchema] = None
    is_learned: bool = False
    is_due_for_review: bool = False
    next_review_at: Optional[datetime] = None


class ReviewSessionSchema(BaseModel):
    """Represents a review session with words to review"""
    lesson_id: int
    words_to_review: List[WordWithProgressSchema]
    new_words: List[WordWithProgressSchema]
    total_words: int
    session_type: str  # "new_lesson", "review_old", "mixed"


class ReviewResultSchema(BaseModel):
    """Result of reviewing a word"""
    word_id: int
    rating: RatingEnum
    success: bool
    next_review_at: Optional[datetime] = None
    fsrs_card_data: Dict[str, Any] = {}
    review_log: Dict[str, Any] = {}


class TelegramWebhookDataSchema(BaseModel):
    user: TelegramUserSchema
    query_id: Optional[str] = None
    auth_date: int
    hash: str


class SuccessResponseSchema(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
