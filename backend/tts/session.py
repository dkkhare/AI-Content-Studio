from __future__ import annotations

from dataclasses import dataclass, field

from datetime import datetime

from pathlib import Path

from uuid import uuid4



@dataclass
class TTSSession:
    """
    Represents one narration generation session.
    """

    id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created: datetime = field(
        default_factory=datetime.now
    )

    started: datetime | None = None

    completed: datetime | None = None

    status: str = "Pending"

    progress: int = 0

    current_chunk: int = 0

    total_chunks: int = 0

    reference_audio: str = ""

    reference_text: str = ""

    input_text: str = ""

    output_directory: str = ""

    output_file: str = ""

    generated_chunks: list[str] = field(
        default_factory=list
    )

    duration: float = 0.0

    error: str = ""

    voice_name: str = ""

    language: str = "en"

    metadata: dict = field(
        default_factory=dict
    )

    cancelled: bool = False
    # ----------------------------------------
    # Session Lifecycle
    # ----------------------------------------

    def start(
        self,
    ):

        self.started = datetime.now()

        self.status = "Running"

        self.progress = 0

        self.cancelled = False

    # ----------------------------------------

    def complete(
        self,
    ):

        self.completed = datetime.now()

        self.status = "Completed"

        self.progress = 100

    # ----------------------------------------

    def fail(
        self,
        message: str,
    ):

        self.completed = datetime.now()

        self.status = "Failed"

        self.error = message

    # ----------------------------------------

    def cancel(
        self,
    ):

        self.completed = datetime.now()

        self.status = "Cancelled"

        self.cancelled = True

    # ----------------------------------------

    def update_progress(
        self,
        current: int,
        total: int,
    ):

        self.current_chunk = current

        self.total_chunks = total

        if total > 0:

            self.progress = int(
                current * 100 / total
            )

        else:

            self.progress = 0

    # ----------------------------------------

    def add_chunk(
        self,
        filename,
    ):

        if filename not in self.generated_chunks:

            self.generated_chunks.append(
                filename
            )
    # ----------------------------------------
    # Properties
    # ----------------------------------------

    @property
    def is_running(
        self,
    ):

        return self.status == "Running"

    @property
    def is_finished(
        self,
    ):

        return self.status in (

            "Completed",

            "Failed",

            "Cancelled",

        )

    @property
    def runtime(
        self,
    ):

        if self.started is None:

            return 0.0

        end_time = (
            self.completed
            if self.completed
            else datetime.now()
        )

        return (
            end_time - self.started
        ).total_seconds()

    # ----------------------------------------
    # Output
    # ----------------------------------------

    def output_path(
        self,
    ):

        if not self.output_file:

            return None

        return Path(
            self.output_file
        )

    def output_exists(
        self,
    ):

        path = self.output_path()

        return (
            path is not None
            and path.exists()
        )

    # ----------------------------------------
    # Statistics
    # ----------------------------------------

    def statistics(
        self,
    ):

        return {

            "id": self.id,

            "status": self.status,

            "progress": self.progress,

            "current_chunk": self.current_chunk,

            "total_chunks": self.total_chunks,

            "generated_chunks": len(
                self.generated_chunks
            ),

            "duration": self.duration,

            "runtime": self.runtime,

            "voice": self.voice_name,

            "language": self.language,

            "output_exists": self.output_exists(),

        }
    # ----------------------------------------
    # Reset
    # ----------------------------------------

    def reset(
        self,
    ):

        self.status = "Pending"

        self.progress = 0

        self.current_chunk = 0

        self.total_chunks = 0

        self.output_file = ""

        self.generated_chunks.clear()

        self.duration = 0.0

        self.error = ""

        self.cancelled = False

        self.started = None

        self.completed = None

    # ----------------------------------------
    # Serialization
    # ----------------------------------------

    def to_dict(
        self,
    ):

        return {

            "id": self.id,

            "created": self.created.isoformat(),

            "started": (
                self.started.isoformat()
                if self.started
                else None
            ),

            "completed": (
                self.completed.isoformat()
                if self.completed
                else None
            ),

            "status": self.status,

            "progress": self.progress,

            "current_chunk": self.current_chunk,

            "total_chunks": self.total_chunks,

            "reference_audio": self.reference_audio,

            "reference_text": self.reference_text,

            "input_text": self.input_text,

            "output_directory": self.output_directory,

            "output_file": self.output_file,

            "generated_chunks": list(
                self.generated_chunks
            ),

            "duration": self.duration,

            "error": self.error,

            "voice_name": self.voice_name,

            "language": self.language,

            "metadata": dict(
                self.metadata
            ),

            "cancelled": self.cancelled,

        }

    # ----------------------------------------

    @classmethod
    def from_dict(
        cls,
        data,
    ):

        session = cls()

        session.id = data.get(
            "id",
            session.id,
        )

        if data.get("created"):

            session.created = datetime.fromisoformat(
                data["created"]
            )

        if data.get("started"):

            session.started = datetime.fromisoformat(
                data["started"]
            )

        if data.get("completed"):

            session.completed = datetime.fromisoformat(
                data["completed"]
            )

        session.status = data.get(
            "status",
            session.status,
        )

        session.progress = data.get(
            "progress",
            0,
        )

        session.current_chunk = data.get(
            "current_chunk",
            0,
        )

        session.total_chunks = data.get(
            "total_chunks",
            0,
        )

        session.reference_audio = data.get(
            "reference_audio",
            "",
        )

        session.reference_text = data.get(
            "reference_text",
            "",
        )

        session.input_text = data.get(
            "input_text",
            "",
        )

        session.output_directory = data.get(
            "output_directory",
            "",
        )

        session.output_file = data.get(
            "output_file",
            "",
        )

        session.generated_chunks = list(
            data.get(
                "generated_chunks",
                [],
            )
        )

        session.duration = data.get(
            "duration",
            0.0,
        )

        session.error = data.get(
            "error",
            "",
        )

        session.voice_name = data.get(
            "voice_name",
            "",
        )

        session.language = data.get(
            "language",
            "en",
        )

        session.metadata = dict(
            data.get(
                "metadata",
                {},
            )
        )

        session.cancelled = data.get(
            "cancelled",
            False,
        )

        return session

    # ----------------------------------------
    # Debug
    # ----------------------------------------

    def debug_info(
        self,
    ):

        return {

            "id": self.id,

            "status": self.status,

            "progress": self.progress,

            "runtime": self.runtime,

            "output": self.output_file,

            "chunks": len(
                self.generated_chunks
            ),

            "cancelled": self.cancelled,

        }