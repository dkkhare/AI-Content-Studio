from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Optional

from backend.tts.session import TTSSession


class TTSQueue:
    """
    Thread-safe queue for TTS sessions.

    Responsibilities
    ----------------
    • Queue management
    • Running session tracking
    • History management
    • Statistics
    """

    def __init__(
        self,
        max_history: int = 100,
    ):

        self._queue = deque()

        self._history = []

        self._current_session: Optional[
            TTSSession
        ] = None

        self._lock = Lock()

        self.max_history = max_history
    # --------------------------------------------------
    # Queue Operations
    # --------------------------------------------------

    def enqueue(
        self,
        session: TTSSession,
    ):

        with self._lock:

            self._queue.append(session)

            return session

    # --------------------------------------------------

    def dequeue(
        self,
    ) -> Optional[TTSSession]:

        with self._lock:

            if not self._queue:

                return None

            session = self._queue.popleft()

            self._current_session = session

            return session

    # --------------------------------------------------

    def peek(
        self,
    ) -> Optional[TTSSession]:

        with self._lock:

            if not self._queue:

                return None

            return self._queue[0]

    # --------------------------------------------------
    # Current Session
    # --------------------------------------------------

    def current(
        self,
    ) -> Optional[TTSSession]:

        with self._lock:

            return self._current_session

    # --------------------------------------------------

    def finish_current(
        self,
    ):

        with self._lock:

            if self._current_session is None:

                return

            self._history.append(
                self._current_session
            )

            if len(self._history) > self.max_history:

                self._history.pop(0)

            self._current_session = None

    # --------------------------------------------------

    def has_current(
        self,
    ) -> bool:

        with self._lock:

            return self._current_session is not None
    # --------------------------------------------------
    # Remove
    # --------------------------------------------------

    def remove(
        self,
        session_id: str,
    ) -> bool:

        with self._lock:

            for session in list(
                self._queue
            ):

                if session.id == session_id:

                    self._queue.remove(
                        session
                    )

                    return True

            if (

                self._current_session
                and
                self._current_session.id == session_id

            ):

                self._current_session = None

                return True

        return False

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def find(
        self,
        session_id: str,
    ) -> Optional[TTSSession]:

        with self._lock:

            if (

                self._current_session
                and
                self._current_session.id == session_id

            ):

                return self._current_session

            for session in self._queue:

                if session.id == session_id:

                    return session

            for session in self._history:

                if session.id == session_id:

                    return session

        return None

    # --------------------------------------------------
    # History
    # --------------------------------------------------

    def history(
        self,
    ):

        with self._lock:

            return list(
                self._history
            )

    # --------------------------------------------------

    def clear_history(
        self,
    ):

        with self._lock:

            self._history.clear()

    # --------------------------------------------------

    def last_session(
        self,
    ) -> Optional[TTSSession]:

        with self._lock:

            if not self._history:

                return None

            return self._history[-1]
    # --------------------------------------------------
    # Information
    # --------------------------------------------------

    def size(
        self,
    ) -> int:

        with self._lock:

            return len(
                self._queue
            )

    # --------------------------------------------------

    def total(
        self,
    ) -> int:

        with self._lock:

            total = len(
                self._queue
            )

            total += len(
                self._history
            )

            if self._current_session:

                total += 1

            return total

    # --------------------------------------------------

    def is_empty(
        self,
    ) -> bool:

        return self.size() == 0

    # --------------------------------------------------

    def clear(
        self,
    ):

        with self._lock:

            self._queue.clear()

            self._history.clear()

            self._current_session = None

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def pending(
        self,
    ):

        with self._lock:

            return [

                session

                for session in self._queue

                if session.status == "Pending"

            ]

    # --------------------------------------------------

    def running(
        self,
    ):

        with self._lock:

            if (

                self._current_session
                and
                self._current_session.status == "Running"

            ):

                return [
                    self._current_session
                ]

            return []

    # --------------------------------------------------

    def completed(
        self,
    ):

        with self._lock:

            return [

                session

                for session in self._history

                if session.status == "Completed"

            ]

    # --------------------------------------------------

    def failed(
        self,
    ):

        with self._lock:

            return [

                session

                for session in self._history

                if session.status == "Failed"

            ]

    # --------------------------------------------------

    def cancelled(
        self,
    ):

        with self._lock:

            return [

                session

                for session in self._history

                if session.status == "Cancelled"

            ]

    # --------------------------------------------------

    def statistics(
        self,
    ):

        return {

            "queued": self.size(),

            "running": len(
                self.running()
            ),

            "completed": len(
                self.completed()
            ),

            "failed": len(
                self.failed()
            ),

            "cancelled": len(
                self.cancelled()
            ),

            "history": len(
                self.history()
            ),

            "total": self.total(),

        }
    # --------------------------------------------------
    # Sessions
    # --------------------------------------------------

    def sessions(
        self,
    ):

        with self._lock:

            return list(
                self._queue
            )

    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        with self._lock:

            return {

                "queued": len(
                    self._queue
                ),

                "history": len(
                    self._history
                ),

                "current": (
                    self._current_session.id
                    if self._current_session
                    else None
                ),

                "max_history": self.max_history,

            }

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):

        with self._lock:

            self._queue.clear()

            self._history.clear()

            self._current_session = None

    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def cleanup(
        self,
    ):

        self.reset()

    # --------------------------------------------------
    # Python Helpers
    # --------------------------------------------------

    def __len__(
        self,
    ):

        return self.size()

    def __bool__(
        self,
    ):

        return not self.is_empty()

    def __iter__(
        self,
    ):

        return iter(
            self.sessions()
        )

    def __contains__(
        self,
        session_id: str,
    ):

        return self.find(
            session_id
        ) is not None