from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, default="en")
    # Streak tracking
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    courses = relationship("Course", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String, nullable=False)  # Target language to learn
    native_language = Column(String, nullable=False)  # User's native language
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)  # Order of lessons in course
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    course = relationship("Course", back_populates="lessons")
    words = relationship("Word", back_populates="lesson", cascade="all, delete-orphan")


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    text = Column(String, nullable=False)  # The word/phrase to learn
    translation = Column(String, nullable=False)  # Translation in native language
    pronunciation = Column(String, nullable=True)  # IPA or pronunciation guide
    example_sentence = Column(Text, nullable=True)  # Example usage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lesson = relationship("Lesson", back_populates="words")
    user_words = relationship("UserWord", back_populates="word", cascade="all, delete-orphan")


class UserWord(Base):
    """Tracks user's progress with specific words using FSRS"""
    __tablename__ = "user_words"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)
    fsrs_card_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    word = relationship("Word", back_populates="user_words")
    reviews = relationship("Review", back_populates="user_word", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_word_id = Column(Integer, ForeignKey("user_words.id"), nullable=False)

    # FSRS Review data
    rating = Column(Integer, nullable=False)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    review_datetime = Column(DateTime(timezone=True), server_default=func.now())
    # TODO: add scheduled_to or due
    scheduled_days = Column(Integer, nullable=True)  # Days until next review
    elapsed_days = Column(Integer, nullable=True)  # Days since last review
    review = Column(Integer, nullable=True)  # Review count
    lapses = Column(Integer, nullable=True)  # Number of times forgot

    # Additional metadata
    lesson_context = Column(Integer, ForeignKey("lessons.id"), nullable=True)  # Which lesson this review was in
    response_time_seconds = Column(Float, nullable=True)  # Time taken to answer

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user_word = relationship("UserWord", back_populates="reviews")
    lesson = relationship("Lesson")


class LessonProgress(Base):
    """Tracks user's progress through lessons"""
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)

    # Progress tracking
    words_learned = Column(Integer, default=0)  # Words marked as "learned"
    words_to_review = Column(Integer, default=0)  # Words marked as "to learn"
    total_words = Column(Integer, nullable=False)

    # Lesson completion
    is_started = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    lesson = relationship("Lesson")
