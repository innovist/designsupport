"""
In-memory chat session store
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

_chat_sessions: Dict[int, Dict[str, Any]] = {}
_chat_messages: Dict[int, List[Dict[str, Any]]] = {}
_chat_session_counter = 1
_chat_message_counter = 1


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def create_chat_session(project_id: int, title: Optional[str] = None) -> Dict[str, Any]:
    global _chat_session_counter
    session_id = _chat_session_counter
    _chat_session_counter += 1

    session = {
        "id": session_id,
        "project_id": project_id,
        "title": title or None,
        "created_at": _now_iso(),
        "updated_at": _now_iso()
    }
    _chat_sessions[session_id] = session
    _chat_messages[session_id] = []
    return session


def list_chat_sessions() -> List[Dict[str, Any]]:
    sessions = list(_chat_sessions.values())
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions


def get_chat_session(session_id: int) -> Optional[Dict[str, Any]]:
    return _chat_sessions.get(session_id)


def add_chat_message(session_id: int, role: str, message: str) -> Dict[str, Any]:
    global _chat_message_counter
    msg = {
        "id": _chat_message_counter,
        "session_id": session_id,
        "role": role,
        "message": message,
        "created_at": _now_iso()
    }
    _chat_message_counter += 1
    _chat_messages.setdefault(session_id, []).append(msg)

    session = _chat_sessions.get(session_id)
    if session:
        session["updated_at"] = _now_iso()

    return msg


def list_chat_messages(session_id: int) -> List[Dict[str, Any]]:
    return list(_chat_messages.get(session_id, []))


def get_chat_session_count() -> int:
    return len(_chat_sessions)


def get_chat_sessions_snapshot() -> List[Dict[str, Any]]:
    return list(_chat_sessions.values())
