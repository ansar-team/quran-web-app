from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    RatingEnum, ReviewSessionSchema, WordWithProgressSchema,
    LessonProgressUpdateSchema, LessonProgressCreateSchema,
    LessonProgressSchema, WordRatingSchema, WordSchema
)
from app.crud import UserWordCRUD, LessonProgressCRUD, WordCRUD
from app.fsrs_service import WordLearningService
from app.utils.session_store import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])


def update_lesson_progress(db: Session, user_id: int, rating_data: dict, new_review: int, learning_service):
    lesson_words = WordCRUD.get_lesson_words(db, rating_data["lesson_id"], user_id)
    total_words = len(lesson_words)

    if total_words == 0:
        return

    words_learned = 0
    if rating_data["rating"] >= 2:
        words_learned = 1

    lesson_progress = LessonProgressCRUD.get_lesson_progress(db, user_id, rating_data["lesson_id"])

    if not lesson_progress:
        progress_data = LessonProgressCreateSchema(
            lesson_id=rating_data["lesson_id"],
            total_words=total_words,
            words_learned=words_learned,
            words_to_review=new_review - words_learned,
            is_started=True,
            is_completed=False
        )
        LessonProgressCRUD.create_lesson_progress(db, progress_data, user_id)
    else:
        is_completed = words_learned >= total_words
        progress_update = LessonProgressUpdateSchema(
            words_learned=(lesson_progress.words_learned + words_learned),
            # TODO: remove words_to_review field or update its calculation, logic is wrong
            words_to_review=(lesson_progress.words_to_review - (1 - words_learned)),
            total_words=total_words,
            is_completed=is_completed
        )
        LessonProgressCRUD.update_lesson_progress(db, user_id, rating_data["lesson_id"], progress_update)


@router.post("/streak", response_model=dict)
def update_user_streak_on_success(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
    today = datetime.now(timezone.utc).date()

    current_streak = current_user.current_streak or 0
    longest_streak = current_user.longest_streak or 0

    if current_user.last_active_date is None:
        current_streak = 1
        longest_streak = max(longest_streak, current_streak)
        current_user.last_active_date = today
    elif current_user.last_active_date == today:
        pass
    else:
        if (today.toordinal() - current_user.last_active_date.toordinal()) == 1:
            current_streak = current_streak + 1
        else:
            current_streak = 1
        longest_streak = max(longest_streak, current_streak)
        current_user.last_active_date = today

    current_user.current_streak = current_streak
    current_user.longest_streak = longest_streak
    db.commit()
    db.refresh(current_user)
    return {
        "current_streak": current_streak,
    }


@router.get("/session/lesson/{lesson_id}", response_model=ReviewSessionSchema)
async def get_review_session(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get a review session for a lesson"""
    try:
        lesson_words = WordCRUD.get_lesson_words(db, lesson_id, current_user.id)

        words = []
        # TODO: think about words learning, should it be like, display first started words and when the new ones, or
        # display all (mixed - in random order), or display them as list (as they added to the lesson)
        # probably the last one is the most correct

        for word in lesson_words:
            word_dict = {
                "id": word.id,
                "text": word.text,
                "translation": word.translation,
                "pronunciation": word.pronunciation,
                "example_sentence": word.example_sentence,
                "lesson_id": word.lesson_id,
                "created_at": word.created_at,
                "updated_at": word.updated_at
            }
            words.append(word_dict)

        return ReviewSessionSchema(
            lesson_id=lesson_id,
            words=words,
            total_words=len(lesson_words)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating review session: {str(e)}"
        )


@router.post("/rate")
async def rate_word_simple(
        rating_data: WordRatingSchema,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Rate a word and update lesson progress"""
    try:
        print(rating_data)
        learning_service = WordLearningService(db)
        new_review = 0

        user_word = UserWordCRUD.get_user_word(db, current_user.id, rating_data.word_id)
        if not user_word:
            user_word = learning_service.create_user_word(current_user.id, rating_data.word_id)
            new_review = 1

        updated_user_word, review = learning_service.review_word(
            user_word,
            RatingEnum(rating_data.rating),
            response_time_seconds=None,
            lesson_context=rating_data.lesson_id
        )

        if rating_data.lesson_id:
            update_lesson_progress(
                db,
                current_user.id,
                rating_data.dict(),
                new_review,
                learning_service
            )
        return

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rating word: {str(e)}"
        )


@router.get("/progress/lesson/{lesson_id}", response_model=LessonProgressSchema)
async def get_lesson_progress(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    lesson_progress = LessonProgressCRUD.get_lesson_progress(db, current_user.id, lesson_id)
    if not lesson_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress found"
        )

    progress_percentage = (lesson_progress.words_learned / lesson_progress.total_words * 100) if lesson_progress.total_words > 0 else 0

    return LessonProgressSchema(
        is_completed=lesson_progress.is_completed,
        total_words=lesson_progress.total_words,
        words_learned=lesson_progress.words_learned,
        progress_percentage=progress_percentage
    )


@router.post("/lesson/{lesson_id}/start", response_model=dict)
async def start_lesson(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Mark a lesson as started"""
    # Get or create lesson progress
    lesson_progress = LessonProgressCRUD.get_lesson_progress(db, current_user.id, lesson_id)

    if not lesson_progress:
        # Get total words
        lesson_words = WordCRUD.get_lesson_words(db, lesson_id, current_user.id)
        total_words = len(lesson_words)

        # Create lesson progress
        progress_data = LessonProgressCreateSchema(
            lesson_id=lesson_id,
            total_words=total_words,
            words_learned=0,
            words_to_review=0,
            is_started=True,
            is_completed=False
        )
        lesson_progress = LessonProgressCRUD.create_lesson_progress(db, progress_data, current_user.id)

    return {
        "lesson_id": lesson_id,
        "is_started": lesson_progress.is_started,
        "message": "Lesson started successfully"
    }


@router.get("/due", response_model=dict)
async def get_words_due_for_review(
        limit: int = 20,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all words due for review across all lessons"""
    learning_service = WordLearningService(db)

    due_user_words = learning_service.get_words_due_for_review(current_user.id, limit)

    result = []
    for user_word in due_user_words:
        word = WordCRUD.get_word(db, user_word.word_id, current_user.id)
        if word:
            result.append(word.to_dict())
    return {"words": result}
