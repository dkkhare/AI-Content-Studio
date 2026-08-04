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

    metadata: dict = field(
        default_factory=dict
    )

    # ----------------------------------------

    def start(self):

        self.status = "Running"

    # ----------------------------------------

    def complete(self):

        self.status = "Completed"

        self.progress = 100

    # ----------------------------------------

    def fail(
        self,
        message: str,
    ):

        self.status = "Failed"

        self.error = message

    # ----------------------------------------

    def cancel(self):

        self.status = "Cancelled"

    # ----------------------------------------

    def update_progress(
        self,
        current,
        total,
    ):

        self.current_chunk = current

        self.total_chunks = total

        if total:

            self.progress = int(
                current * 100 / total
            )

    # ----------------------------------------

    def add_chunk(
        self,
        filename,
    ):

        self.generated_chunks.append(
            filename
        )

    # ----------------------------------------

    @property
    def is_running(self):

        return self.status == "Running"

    @property
    def is_finished(self):

        return self.status in (

            "Completed",

            "Failed",

            "Cancelled",

        )

    # ----------------------------------------

    def output_path(self):

        if not self.output_file:

            return None

        return Path(
            self.output_file
        )