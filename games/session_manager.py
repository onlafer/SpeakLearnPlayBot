from .base import GameStatus


class SessionManager:
    def __init__(self):
        self._active_sessions = {}

    def start_session(self, session):
        self._active_sessions[session.user_id] = session

    def get_session(self, user_id):
        return self._active_sessions.get(user_id)

    def has_active_session(self, user_id: int) -> bool:
        """Checks if a user has a game that is currently in progress."""
        session = self.get_session(user_id)
        return session and session.status == GameStatus.IN_PROGRESS

    def update_session(self, user_id, session):
        if user_id in self._active_sessions:
            self._active_sessions[user_id] = session
    
    def end_session(self, user_id):
        if user_id in self._active_sessions:
            del self._active_sessions[user_id]

session_manager = SessionManager()
