from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fsrs import Scheduler, Card, Rating, ReviewLog
from app.schemas import RatingEnum, StateEnum, UserWordSchema, ReviewSchema
from app.models import UserWord, Review
from sqlalchemy.orm import Session


class FSRSManager:
    """Manages FSRS (Free Spaced Repetition Scheduler) integration"""
    def __init__(self):
        self.scheduler = Scheduler()

    def review_card(self, user_word: UserWordSchema, rating: RatingEnum,
                    response_time_seconds: Optional[float] = None) -> tuple[Dict[str, Any], Dict[str, Any]]:
        # Prepare data
        card = Card.from_dict(user_word.fsrs_card_data)
        fsrs_rating = Rating(rating.value)

        # Review the card
        card, review_log = self.scheduler.review_card(
            card, fsrs_rating, datetime.now(timezone.utc), response_time_seconds)

        # Convert back to dictionaries
        updated_card_data = card.to_dict()
        review_log_data = review_log.to_dict()

        return updated_card_data, review_log_data

    def get_card_retrievability(self, user_word: UserWordSchema) -> float:
        """Get the current retrievability (probability of recall) for a card"""
        card = Card.from_dict(user_word.fsrs_card_data)
        return self.scheduler.get_card_retrievability(card)

    def is_card_due(self, user_word: UserWordSchema) -> bool:
        """Check if a card is due for review"""
        card = Card.from_dict(user_word.fsrs_card_data)
        now = datetime.now(timezone.utc)
        return card.due <= now

    def get_next_review_time(self, user_word: UserWordSchema) -> Optional[datetime]:
        """Get the next review time for a card"""
        card = Card.from_dict(user_word.fsrs_card_data)
        return card.due

    def get_card_state(self, user_word: UserWordSchema) -> StateEnum:
        """Get the current state of a card"""
        card = Card.from_dict(user_word.fsrs_card_data)
        return StateEnum(card.state)

    def reschedule_card(self, user_word: UserWordSchema, review_logs: list[ReviewLog]) -> Dict[str, Any]:
        """Reschedule a card based on historical review logs"""
        card = Card.from_dict(user_word.fsrs_card_data)
        rescheduled_card = self.scheduler.reschedule_card(card, review_logs)
        return rescheduled_card.to_dict()


class WordLearningService:
    """Service for managing word learning with FSRS"""
    def __init__(self, db: Session):
        self.db = db
        self.fsrs_manager = FSRSManager()

    def create_user_word(self, user_id: int, word_id: int) -> Optional[UserWordSchema]:
        card = Card()
        user_word = UserWord(
            user_id=user_id,
            word_id=word_id,
            fsrs_card_data=card.to_dict()
        )
        self.db.add(user_word)
        self.db.commit()
        self.db.refresh(user_word)

        return UserWordSchema.model_validate(user_word)


    def review_word(self, user_word: UserWordSchema, rating: RatingEnum,
                    response_time_seconds: Optional[float] = None,
                    lesson_context: Optional[int] = None) -> tuple[UserWordSchema, ReviewSchema]:
        # Update FSRS card
        updated_card_data, review_log_data = self.fsrs_manager.review_card(
            user_word, rating, response_time_seconds
        )

        # Update user word
        user_word.fsrs_card_data = updated_card_data

        # Create review log
        review = Review(
            user_word_id=user_word.id,
            rating=rating.value,
            review_datetime=datetime.fromisoformat(review_log_data["review_datetime"].replace('Z', '+00:00')),
            # TODO: add due field
            # due=updated_card_data.get("due"),
            lesson_context=lesson_context,
            response_time_seconds=response_time_seconds
        )

        word_query = self.db.query(UserWord).filter(UserWord.id == user_word.id)
        word_query.update({
            'fsrs_card_data': user_word.fsrs_card_data
        }, synchronize_session=False)

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        return UserWordSchema.model_validate(word_query.first()), ReviewSchema.model_validate(review)


    def get_words_due_for_review(self, user_id: int, limit: int = 20) -> list[UserWordSchema]:
        """Get words that are due for review"""
        user_words = self.db.query(UserWord).filter(
            UserWord.user_id == user_id
        ).all()

        due_words = []
        for user_word in user_words:
            if self.fsrs_manager.is_card_due(UserWordSchema.model_validate(user_word)):
                due_words.append(UserWordSchema.model_validate(user_word))

        due_words.sort(key=lambda uw: self.fsrs_manager.get_next_review_time(uw))

        return due_words[:limit]
