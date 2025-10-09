from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from app.models import User, Course, Lesson, Word
from app.schemas import (
    UserCreate, CourseCreate, CourseUpdate, LessonCreate, LessonUpdate,
    WordCreate, WordUpdate
)


class UserCRUD:
    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
        return db.query(User).filter(User.telegram_id == telegram_id).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        db_user = User(**user_data.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                setattr(user, key, value)
            db.commit()
            db.refresh(user)
        return user


class CourseCRUD:
    @staticmethod
    def get_user_courses(db: Session, user_id: int) -> List[Course]:
        return db.query(Course).filter(Course.user_id == user_id).order_by(desc(Course.created_at)).all()

    @staticmethod
    def get_course(db: Session, course_id: int, user_id: int) -> Optional[Course]:
        return db.query(Course).filter(
            and_(Course.id == course_id, Course.user_id == user_id)
        ).first()

    @staticmethod
    def create_course(db: Session, course_data: CourseCreate, user_id: int) -> Course:
        db_course = Course(**course_data.dict(), user_id=user_id)
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return db_course

    @staticmethod
    def update_course(db: Session, course_id: int, user_id: int, course_data: CourseUpdate) -> Optional[Course]:
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
    def get_course_lessons(db: Session, course_id: int, user_id: int) -> List[Lesson]:
        return db.query(Lesson).join(Course).filter(
            and_(Lesson.course_id == course_id, Course.user_id == user_id)
        ).order_by(asc(Lesson.order_index)).all()

    @staticmethod
    def get_lesson(db: Session, lesson_id: int, user_id: int) -> Optional[Lesson]:
        return db.query(Lesson).join(Course).filter(
            and_(Lesson.id == lesson_id, Course.user_id == user_id)
        ).first()

    @staticmethod
    def create_lesson(db: Session, lesson_data: LessonCreate, course_id: int) -> Lesson:
        db_lesson = Lesson(**lesson_data.dict(), course_id=course_id)
        db.add(db_lesson)
        db.commit()
        db.refresh(db_lesson)
        return db_lesson

    @staticmethod
    def update_lesson(db: Session, lesson_id: int, user_id: int, lesson_data: LessonUpdate) -> Optional[Lesson]:
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
    def get_lesson_words(db: Session, lesson_id: int, user_id: int) -> List[Word]:
        return db.query(Word).join(Lesson).join(Course).filter(
            and_(Word.lesson_id == lesson_id, Course.user_id == user_id)
        ).order_by(asc(Word.order_index)).all()

    @staticmethod
    def get_word(db: Session, word_id: int, user_id: int) -> Optional[Word]:
        return db.query(Word).join(Lesson).join(Course).filter(
            and_(Word.id == word_id, Course.user_id == user_id)
        ).first()

    @staticmethod
    def create_word(db: Session, word_data: WordCreate, lesson_id: int) -> Word:
        db_word = Word(**word_data.dict(), lesson_id=lesson_id)
        db.add(db_word)
        db.commit()
        db.refresh(db_word)
        return db_word

    @staticmethod
    def update_word(db: Session, word_id: int, user_id: int, word_data: WordUpdate) -> Optional[Word]:
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
