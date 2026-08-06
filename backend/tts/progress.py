from __future__ import annotations

from dataclasses import dataclass

from datetime import datetime


@dataclass
class TTSProgress:
    """
    Progress information for narration generation.
    """

    stage: str = ""

    status: str = ""

    current_chunk: int = 0

    total_chunks: int = 0

    current_text: str = ""

    percent: int = 0

    elapsed_seconds: float = 0.0

    remaining_seconds: float = 0.0

    output_file: str = ""

    speed: float = 0.0

    started: datetime | None = None

    message: str = ""
    # --------------------------------------------------
    # Progress
    # --------------------------------------------------

    def update_percent(
        self,
    ) -> int:

        if self.total_chunks <= 0:

            self.percent = 0

        else:

            self.percent = min(

                100,

                int(

                    self.current_chunk
                    * 100
                    / self.total_chunks

                ),

            )

        return self.percent

    # --------------------------------------------------
    # Start
    # --------------------------------------------------

    def start(
        self,
    ):

        self.started = datetime.now()

        self.status = "Running"

        self.percent = 0

    # --------------------------------------------------
    # Timing
    # --------------------------------------------------

    def update_time(
        self,
    ):

        if self.started is None:

            return

        self.elapsed_seconds = (

            datetime.now() - self.started

        ).total_seconds()

        if (

            self.percent > 0

            and

            self.percent < 100

        ):

            total = (

                self.elapsed_seconds
                * 100
                / self.percent

            )

            self.remaining_seconds = max(

                0.0,

                total - self.elapsed_seconds,

            )

    # --------------------------------------------------
    # Finish
    # --------------------------------------------------

    def finish(
        self,
    ):

        self.status = "Completed"

        self.percent = 100

        self.remaining_seconds = 0.0

        self.update_time()

    # --------------------------------------------------
    # Reset
    # --------------------------------------------------

    def reset(
        self,
    ):

        self.stage = ""

        self.status = ""

        self.current_chunk = 0

        self.total_chunks = 0

        self.current_text = ""

        self.percent = 0

        self.elapsed_seconds = 0.0

        self.remaining_seconds = 0.0

        self.output_file = ""

        self.speed = 0.0

        self.started = None

        self.message = ""
    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def statistics(
        self,
    ):

        return {

            "stage": self.stage,

            "status": self.status,

            "percent": self.percent,

            "current_chunk": self.current_chunk,

            "total_chunks": self.total_chunks,

            "elapsed_seconds": self.elapsed_seconds,

            "remaining_seconds": self.remaining_seconds,

            "speed": self.speed,

            "output_file": self.output_file,

            "message": self.message,

        }

    # --------------------------------------------------
    # Serialization
    # --------------------------------------------------

    def to_dict(
        self,
    ):

        return {

            "stage": self.stage,

            "status": self.status,

            "current_chunk": self.current_chunk,

            "total_chunks": self.total_chunks,

            "current_text": self.current_text,

            "percent": self.percent,

            "elapsed_seconds": self.elapsed_seconds,

            "remaining_seconds": self.remaining_seconds,

            "output_file": self.output_file,

            "speed": self.speed,

            "started": (
                self.started.isoformat()
                if self.started
                else None
            ),

            "message": self.message,

        }

    # --------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data,
    ):

        progress = cls()

        progress.stage = data.get(
            "stage",
            "",
        )

        progress.status = data.get(
            "status",
            "",
        )

        progress.current_chunk = data.get(
            "current_chunk",
            0,
        )

        progress.total_chunks = data.get(
            "total_chunks",
            0,
        )

        progress.current_text = data.get(
            "current_text",
            "",
        )

        progress.percent = data.get(
            "percent",
            0,
        )

        progress.elapsed_seconds = data.get(
            "elapsed_seconds",
            0.0,
        )

        progress.remaining_seconds = data.get(
            "remaining_seconds",
            0.0,
        )

        progress.output_file = data.get(
            "output_file",
            "",
        )

        progress.speed = data.get(
            "speed",
            0.0,
        )

        progress.message = data.get(
            "message",
            "",
        )

        started = data.get(
            "started"
        )

        if started:

            progress.started = datetime.fromisoformat(
                started
            )

        return progress

    # --------------------------------------------------
    # Debug
    # --------------------------------------------------

    def debug_info(
        self,
    ):

        return {

            "stage": self.stage,

            "status": self.status,

            "percent": self.percent,

            "elapsed": self.elapsed_seconds,

            "remaining": self.remaining_seconds,

            "chunk": (
                f"{self.current_chunk}/"
                f"{self.total_chunks}"
            ),

        }