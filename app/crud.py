from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from app.models import User, Course, Lesson, Word, UserWord, LessonProgress
from app.schemas import (
    UserCreateSchema, UserSchema, CourseCreateSchema, CourseUpdateSchema, CourseSchema,
    LessonCreateSchema, LessonUpdateSchema, LessonSchema, WordCreateSchema,
    WordUpdateSchema, WordSchema, LessonProgressCreateSchema, LessonProgressUpdateSchema,
    LessonProgressSchema, UserWordSchema
)


class UserCRUD:
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
        return db.query(User).filter(User.telegram_id == telegram_id).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreateSchema) -> UserSchema:
        db_user = UserSchema(**user_data.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[UserSchema]:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user


class CourseCRUD:
    @staticmethod
    def get_user_courses(db: Session, user_id: int) -> List[CourseSchema]:
        return db.query(Course).filter(Course.user_id == user_id).order_by(desc(Course.created_at)).all()

    @staticmethod
    def get_course(db: Session, course_id: int, user_id: int) -> Optional[CourseSchema]:
        return db.query(Course).filter(
            and_(Course.id == course_id, Course.user_id == user_id)
        ).first()

    @staticmethod
    def create_course(db: Session, course_data: CourseCreateSchema, user_id: int) -> CourseSchema:
        db_course = Course(**course_data.__dict__, user_id=user_id)
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return CourseSchema.model_validate(db_course)

    @staticmethod
    def update_course(db: Session, course_id: int, user_id: int, course_data: CourseUpdateSchema) -> Optional[CourseSchema]:
        course = db.query(Course).filter(
            and_(Course.id == course_id, Course.user_id == user_id)
        ).first()
        if course:
            update_data = course_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(course, key, value)
            db.commit()
            db.refresh(course)
        return course

    @staticmethod
    def delete_course(db: Session, course_id: int, user_id: int) -> bool:
        course = db.query(Course).filter(
            and_(Course.id == course_id, Course.user_id == user_id)
        ).first()
        if course:
            db.delete(course)
            db.commit()
            return True
        return False


class LessonCRUD:
    @staticmethod
    def get_course_lessons(db: Session, course_id: int, user_id: int) -> List[LessonSchema]:
        return db.query(Lesson).join(Course).filter(
            and_(Lesson.course_id == course_id, Course.user_id == user_id)
        ).order_by(asc(Lesson.order_index)).all()

    @staticmethod
    def get_lesson(db: Session, lesson_id: int, user_id: int) -> Optional[LessonSchema]:
        return db.query(Lesson).join(Course).filter(
            and_(Lesson.id == lesson_id, Course.user_id == user_id)
        ).first()

    @staticmethod
    def create_lesson(db: Session, lesson_data: LessonCreateSchema) -> LessonSchema:
        db_lesson = Lesson(**lesson_data.__dict__)
        db.add(db_lesson)
        db.commit()
        db.refresh(db_lesson)
        return LessonSchema.model_validate(db_lesson)

    @staticmethod
    def update_lesson(db: Session, lesson_id: int, user_id: int, lesson_data: LessonUpdateSchema) -> Optional[LessonSchema]:
        lesson = db.query(Lesson).join(Course).filter(
            and_(Lesson.id == lesson_id, Course.user_id == user_id)
        ).first()
        if lesson:
            update_data = lesson_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(lesson, key, value)
            db.commit()
            db.refresh(lesson)
        return lesson

    @staticmethod
    def delete_lesson(db: Session, lesson_id: int, user_id: int) -> bool:
        lesson = db.query(Lesson).join(Course).filter(
            and_(Lesson.id == lesson_id, Course.user_id == user_id)
        ).first()
        if lesson:
            db.delete(lesson)
            db.commit()
            return True
        return False


class WordCRUD:
    @staticmethod
    def get_lesson_words(db: Session, lesson_id: int, user_id: int) -> List[WordSchema]:
        return db.query(Word).join(Lesson).join(Course).filter(
            and_(Word.lesson_id == lesson_id, Course.user_id == user_id)
        ).order_by(asc(Word.order_index)).all()

    @staticmethod
    def get_word(db: Session, word_id: int, user_id: int) -> Optional[WordSchema]:
        return db.query(Word).join(Lesson).join(Course).filter(
            and_(Word.id == word_id, Course.user_id == user_id)
        ).first()

    @staticmethod
    def create_word(db: Session, word_data: WordCreateSchema, lesson_id: int) -> WordSchema:
        db_word = Word(**word_data.__dict__, lesson_id=lesson_id)
        db.add(db_word)
        db.commit()
        db.refresh(db_word)
        return WordSchema.model_validate(db_word)

    @staticmethod
    def update_word(db: Session, word_id: int, user_id: int, word_data: WordUpdateSchema) -> Optional[WordSchema]:
        word = db.query(Word).join(Lesson).join(Course).filter(
            and_(Word.id == word_id, Course.user_id == user_id)
        ).first()
        if word:
            update_data = word_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(word, key, value)
            db.commit()
            db.refresh(word)
        return word

    @staticmethod
    def delete_word(db: Session, word_id: int, user_id: int) -> bool:
        word = db.query(Word).join(Lesson).join(Course).filter(
            and_(Word.id == word_id, Course.user_id == user_id)
        ).first()
        if word:
            db.delete(word)
            db.commit()
            return True
        return False


class UserWordCRUD:
    @staticmethod
    def get_user_word(db: Session, user_id: int, word_id: int) -> Optional[UserWordSchema]:
        return db.query(UserWord).filter(
            and_(UserWord.user_id == user_id, UserWord.word_id == word_id)
        ).first()

    @staticmethod
    def get_user_words_by_lesson(db: Session, user_id: int, lesson_id: int) -> List[UserWordSchema]:
        return db.query(UserWord).join(Word).filter(
            and_(UserWord.user_id == user_id, Word.lesson_id == lesson_id)
        ).all()

    @staticmethod
    def get_user_words_due(db: Session, user_id: int, limit: int = 20) -> List[UserWordSchema]:
        # This will be enhanced with FSRS logic
        return db.query(UserWord).filter(UserWord.user_id == user_id).limit(limit).all()


class LessonProgressCRUD:
    @staticmethod
    def get_lesson_progress(db: Session, user_id: int, lesson_id: int) -> Optional[LessonProgressSchema]:
        return db.query(LessonProgress).filter(
            and_(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        ).first()

    @staticmethod
    def create_lesson_progress(db: Session, progress_data: LessonProgressCreateSchema, user_id: int) -> LessonProgressCreateSchema:
        db_progress = LessonProgress(**progress_data.__dict__, user_id=user_id)
        db.add(db_progress)
        db.commit()
        db.refresh(db_progress)
        return LessonProgressCreateSchema.model_validate(db_progress)

    @staticmethod
    def update_lesson_progress(db: Session, user_id: int, lesson_id: int,
                               progress_data: LessonProgressUpdateSchema) -> Optional[LessonProgressSchema]:
        progress = db.query(LessonProgress).filter(
            and_(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        ).first()
        if progress:
            update_data = progress_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(progress, key, value)
            # Update timestamps
            if update_data.get('is_started') and not progress.started_at:
                progress.started_at = datetime.now(timezone.utc)
            if update_data.get('is_completed') and not progress.completed_at:
                progress.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(progress)
        return LessonProgressSchema.model_validate(progress)

    @staticmethod
    def get_user_progress_summary(db: Session, user_id: int) -> dict:
        """Get overall progress summary for a user"""
        total_lessons = db.query(LessonProgress).filter(LessonProgress.user_id == user_id).count()
        completed_lessons = db.query(LessonProgress).filter(
            and_(LessonProgress.user_id == user_id, LessonProgress.is_completed == True)
        ).count()

        total_words = db.query(UserWord).filter(UserWord.user_id == user_id).count()
        words_due = db.query(UserWord).filter(
            and_(UserWord.user_id == user_id, UserWord.last_reviewed_at.isnot(None))
        ).count()

        return {
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "total_words": total_words,
            "words_due_for_review": words_due
        }
