import time
import uuid

from fastapi import Cookie, HTTPException, Depends
from sqlalchemy.orm import Session

from app.crud import UserCRUD
from app.database import get_db

SESSION_TTL = 15 * 60

_sessions: dict[str, dict] = {}


def create_session(user_id: int) -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = {
        "user_id": user_id,
        "expires_at": time.time() + SESSION_TTL
    }
    return session_id


def get_session(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return None

    if session["expires_at"] < time.time():
        _sessions.pop(session_id, None)
        return None

    return session


def delete_session(session_id: str):
    _sessions.pop(session_id, None)


def get_current_user(
        session_id: str | None = Cookie(default=None),
        db: Session = Depends(get_db)
):
    if not session_id:
        raise HTTPException(status_code=401)
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=401)

    existing_user = UserCRUD.get_user_by_telegram_id(db, session.get("user_id"))

    return existing_user
