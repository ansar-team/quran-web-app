from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import (
    RatingEnum, ReviewSessionSchema, WordWithProgressSchema,
    LessonProgressUpdateSchema, LessonProgressCreateSchema, UserSchema
)
from pydantic import BaseModel
from app.crud import UserWordCRUD, LessonProgressCRUD, LessonCRUD, WordCRUD
from app.fsrs_service import WordLearningService
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/reviews", tags=["reviews"])


# TODO: move this logic to class or utils?
def update_lesson_progress(db: Session, user_id: int, lesson_id: int, learning_service):
    """Update lesson progress based on reviewed words"""
    print(f"DEBUG: update_lesson_progress called - user_id: {user_id}, lesson_id: {lesson_id}")

    # Get all words in the lesson
    # TODO: consider providing lesson data from the function which calls this one
    lesson_words = WordCRUD.get_lesson_words(db, lesson_id, user_id)
    total_words = len(lesson_words)
    print(f"DEBUG: Found {total_words} words in lesson {lesson_id}")

    if total_words == 0:
        print("DEBUG: No words in lesson, skipping progress update")
        return

    # Count how many words have been reviewed
    words_reviewed = 0
    words_learned = 0

    # TODO: can it be done better in caller functions? why check it here
    for word in lesson_words:
        user_word = UserWordCRUD.get_user_word(db, user_id, word.id)
        if user_word:
            words_reviewed += 1
            # Check if word is in "Review" state (state 2) or better
            progress = learning_service.get_word_progress(user_word)
            if progress.get("state") and progress["state"].value >= 2:
                words_learned += 1

    print(f"DEBUG: Progress stats - reviewed: {words_reviewed}, learned: {words_learned}")

    # Get or create lesson progress
    lesson_progress = LessonProgressCRUD.get_lesson_progress(db, user_id, lesson_id)
    print(f"DEBUG: Existing lesson progress: {lesson_progress is not None}")

    if not lesson_progress:
        # Create new lesson progress
        print("DEBUG: Creating new lesson progress")
        progress_data = LessonProgressCreateSchema(
            lesson_id=lesson_id,
            total_words=total_words,
            words_learned=words_learned,
            words_to_review=words_reviewed - words_learned,
            is_started=True,
            is_completed=False
        )
        LessonProgressCRUD.create_lesson_progress(db, progress_data, user_id)
    else:
        # Mark as completed if all words are learned
        is_completed = words_learned >= total_words
        print(f"DEBUG: Updating lesson progress, is_completed: {is_completed}")

        progress_update = LessonProgressUpdateSchema(
            words_learned=words_learned,
            words_to_review=words_reviewed - words_learned,
            total_words=total_words,
            is_completed=is_completed
        )
        LessonProgressCRUD.update_lesson_progress(db, user_id, lesson_id, progress_update)


@router.post("/streak", response_model=dict)
def update_user_streak_on_success(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
    today = datetime.now(timezone.utc).date()

    # Initialize counters if missing
    current_streak = current_user.current_streak or 0
    longest_streak = current_user.longest_streak or 0

    if current_user.last_active_date is None:
        current_streak = 1
        longest_streak = max(longest_streak, current_streak)
        current_user.last_active_date = today
    elif current_user.last_active_date == today:
        # Already counted today; no change
        pass
    else:
        # If the user was active exactly yesterday, continue the streak
        if (today.toordinal() - current_user.last_active_date.toordinal()) == 1:
            current_streak = current_streak + 1
        else:
            # Missed at least one day, reset streak
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


# TODO: move this to schemas
class WordRatingSchema(BaseModel):
    """Schema for rating a word"""
    word_id: int
    rating: int  # 1=Easy, 2=Medium, 3=Hard, 4=Again
    lesson_id: Optional[int] = None


@router.get("/session/lesson/{lesson_id}", response_model=ReviewSessionSchema)
async def get_review_session(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get a review session for a lesson (new words + words due for review)"""
    print(f"DEBUG: get_review_session called - lesson_id: {lesson_id}, user_id: {current_user.id}")

    try:
        # Get all words in the lesson
        lesson_words = WordCRUD.get_lesson_words(db, lesson_id, current_user.id)
        print(f"DEBUG: Found {len(lesson_words)} words in lesson")

        new_words = []
        words_to_review = []

        # TODO: think of optimization (not good to call db so often)
        for word in lesson_words:
            # Check if user has started learning this word
            user_word = UserWordCRUD.get_user_word(db, current_user.id, word.id)
            print(f"DEBUG: Word {word.id} - user_word exists: {user_word is not None}")

            if not user_word:
                # For now, just add as new word without creating UserWord
                # This avoids the FSRS service issue
                # TODO: create UserWord
                print(f"DEBUG: Adding word {word.id} to new_words")
                word_dict = {
                    "id": word.id,
                    "text": word.text,
                    "translation": word.translation,
                    "pronunciation": word.pronunciation,
                    "example_sentence": word.example_sentence,
                    "difficulty_level": word.difficulty_level,
                    "order_index": word.order_index,
                    "lesson_id": word.lesson_id,
                    "created_at": word.created_at,
                    "updated_at": word.updated_at
                }
                new_words.append(WordWithProgressSchema(
                    **word_dict,
                    user_word=None,
                    is_learned=False,
                    is_due_for_review=False,
                    next_review_at=None
                ))
            else:
                # For existing words, mark as review words for now
                # TODO: use schemas
                print(f"DEBUG: Adding word {word.id} to words_to_review")
                word_dict = {
                    "id": word.id,
                    "text": word.text,
                    "translation": word.translation,
                    "pronunciation": word.pronunciation,
                    "example_sentence": word.example_sentence,
                    "difficulty_level": word.difficulty_level,
                    "order_index": word.order_index,
                    "lesson_id": word.lesson_id,
                    "created_at": word.created_at,
                    "updated_at": word.updated_at
                }
                words_to_review.append(WordWithProgressSchema(
                    **word_dict,
                    user_word=user_word,
                    is_learned=False,
                    is_due_for_review=True,
                    next_review_at=None
                ))

        # Determine session type
        session_type = "mixed"
        if not words_to_review and new_words:
            session_type = "new_lesson"
        elif not new_words and words_to_review:
            session_type = "review_old"

        print(
            f"DEBUG: Session type: {session_type}, new_words: {len(new_words)}, words_to_review: {len(words_to_review)}")

        return ReviewSessionSchema(
            lesson_id=lesson_id,
            words_to_review=words_to_review,
            new_words=new_words,
            total_words=len(lesson_words),
            session_type=session_type
        )

    except Exception as e:
        print(f"ERROR in get_review_session: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
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
        # Convert int rating to RatingEnum
        rating_enum = RatingEnum(rating_data.rating)

        # Initialize FSRS learning service
        learning_service = WordLearningService(db)

        # Get or create user word
        # TODO: do crud operations here for performance?
        user_word = UserWordCRUD.get_user_word(db, current_user.id, rating_data.word_id)

        if not user_word:
            print("DEBUG: Creating new user_word")
            user_word = learning_service.create_user_word(current_user.id, rating_data.word_id)

        # Review the word using FSRS
        print("DEBUG: Calling learning_service.review_word")
        updated_user_word, review = learning_service.review_word(
            user_word,
            rating_enum,
            response_time_seconds=None,
            lesson_context=rating_data.lesson_id
        )
        print(
            f"DEBUG: Review completed - updated_user_word: {updated_user_word is not None}, review: {review is not None}")

        # Update lesson progress if lesson_id provided
        if rating_data.lesson_id:
            print(f"DEBUG: Updating lesson progress for lesson {rating_data.lesson_id}")
            update_lesson_progress(
                db,
                current_user.id,
                rating_data.lesson_id,
                learning_service
            )
        return

    except Exception as e:
        print(f"ERROR in rate_word_simple: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rating word: {str(e)}"
        )


@router.post("/word/{word_id}/review")
async def review_word(
        word_id: int,
        rating: RatingEnum,
        response_time_seconds: Optional[float] = None,
        lesson_context: Optional[int] = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Review a word with the given rating"""
    print(f"DEBUG: review_word called - word_id: {word_id}, rating: {rating}, lesson_context: {lesson_context}")

    learning_service = WordLearningService(db)

    # Verify word belongs to user
    word = WordCRUD.get_word(db, word_id, current_user.id)
    print(f"DEBUG: Word found: {word is not None}")

    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )

    # Get or create user word
    user_word = UserWordCRUD.get_user_word(db, current_user.id, word_id)
    print(f"DEBUG: Existing user_word: {user_word is not None}")

    if not user_word:
        print("DEBUG: Creating new user_word")
        user_word = learning_service.create_user_word(current_user.id, word_id)

    # Review the word
    print("DEBUG: Calling learning_service.review_word")
    updated_user_word, review = learning_service.review_word(
        user_word, rating, response_time_seconds, lesson_context
    )
    print(f"DEBUG: Review completed - updated_user_word: {updated_user_word is not None}, review: {review is not None}")

    return


@router.get("/progress/word/{word_id}", response_model=dict)
async def get_word_progress(
        word_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get detailed progress information for a word"""
    print(f"DEBUG: get_word_progress called - word_id: {word_id}, user_id: {current_user.id}")

    learning_service = WordLearningService(db)

    # Verify word belongs to user
    word = WordCRUD.get_word(db, word_id, current_user.id)
    print(f"DEBUG: Word found: {word is not None}")

    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Word not found"
        )

    # Get user word
    user_word = UserWordCRUD.get_user_word(db, current_user.id, word_id)
    print(f"DEBUG: User word found: {user_word is not None}")

    if not user_word:
        print("DEBUG: No user word found, returning default progress")
        return {
            "word_id": word_id,
            "is_learned": False,
            "total_reviews": 0,
            "correct_reviews": 0,
            "accuracy_rate": 0.0,
            "retrievability": 0.0,
            "next_review_at": None,
            "state": "new"
        }

    progress = learning_service.get_word_progress(user_word)
    print(f"DEBUG: Progress data - state: {progress.get('state')}, is_learned: {progress.get('state') == 2}")

    return {
        "word_id": word_id,
        "is_learned": progress["state"] == 2,
        "total_reviews": progress["total_reviews"],
        "correct_reviews": progress["correct_reviews"],
        "accuracy_rate": progress["accuracy_rate"],
        "retrievability": progress["retrievability"],
        "next_review_at": progress["next_review_at"],
        "state": progress["state"].name.lower()
    }


@router.get("/progress/lesson/{lesson_id}", response_model=dict)
async def get_lesson_progress(
        lesson_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Get lesson progress
    # TODO: retrieve with lesson_progress.id
    lesson_progress = LessonProgressCRUD.get_lesson_progress(db, current_user.id, lesson_id)
    print(f"DEBUG: Lesson progress found: {lesson_progress is not None}")

    if not lesson_progress:

        print("DEBUG: No lesson progress found, returning default")
        lesson_words = WordCRUD.get_lesson_words(db, lesson_id, current_user.id)
        total_words = len(lesson_words)

        return {
            "lesson_id": lesson_id,
            "is_started": False,
            "is_completed": False,
            "total_words": total_words,
            "words_learned": 0,
            "words_to_review": 0,
            "progress_percentage": 0.0
        }

    progress_percentage = (lesson_progress.words_learned / lesson_progress.total_words * 100) if lesson_progress.total_words > 0 else 0
    print(f"DEBUG: Progress percentage: {progress_percentage}%")

    # TODO: use pydantic model
    return {
        "lesson_id": lesson_id,
        "is_started": lesson_progress.is_started,
        "is_completed": lesson_progress.is_completed,
        "total_words": lesson_progress.total_words,
        "words_learned": lesson_progress.words_learned,
        "words_to_review": lesson_progress.words_to_review,
        "progress_percentage": progress_percentage,
        "started_at": lesson_progress.started_at,
        "completed_at": lesson_progress.completed_at
    }


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


# TODO: define response model
@router.get("/due", response_model=dict)
async def get_words_due_for_review(
        limit: int = 20,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get all words due for review across all lessons"""
    print(f"DEBUG: get_words_due_for_review called - limit: {limit}, user_id: {current_user.id}")

    learning_service = WordLearningService(db)

    # Get words due for review
    due_user_words = learning_service.get_words_due_for_review(current_user.id, limit)
    print(f"DEBUG: Found {len(due_user_words)} due words")

    result = []
    for user_word in due_user_words:
        word = WordCRUD.get_word(db, user_word.word_id, current_user.id)
        if word:
            progress = learning_service.get_word_progress(user_word)
            result.append(WordWithProgressSchema(
                **word.__dict__,
                user_word=user_word,
                is_learned=progress["state"] == 2,
                is_due_for_review=progress["is_due"],
                next_review_at=progress["next_review_at"]
            ).__dict__)
    return {"words": result}
