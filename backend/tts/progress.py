from dataclasses import dataclass
from datetime import datetime


@dataclass
class TTSProgress:
    """
    Progress information for TTS generation.
    """

    # --------------------------------------------------
    # Stage
    # --------------------------------------------------

    stage: str = "Initializing"

    status: str = "Waiting"

    # --------------------------------------------------
    # Chunk Progress
    # --------------------------------------------------

    current_chunk: int = 0

    total_chunks: int = 0

    current_text: str = ""

    # --------------------------------------------------
    # Overall Progress
    # --------------------------------------------------

    percent: int = 0

    processed_characters: int = 0

    total_characters: int = 0

    # --------------------------------------------------
    # Timing
    # --------------------------------------------------

    elapsed_seconds: float = 0.0

    remaining_seconds: float = 0.0

    started_at: datetime | None = None

    # --------------------------------------------------
    # Audio
    # --------------------------------------------------

    generated_audio_seconds: float = 0.0

    sample_rate: int = 24000

    # --------------------------------------------------
    # Device
    # --------------------------------------------------

    device: str = ""

    gpu_memory_used_mb: float = 0.0

    # --------------------------------------------------
    # Runtime State
    # --------------------------------------------------

    completed: bool = False

    cancelled: bool = False

    error: str = ""

    # --------------------------------------------------
    # Helper Methods
    # --------------------------------------------------

    def update_percent(self):

        if self.total_chunks > 0:

            self.percent = int(
                (self.current_chunk / self.total_chunks) * 100
            )

        else:

            self.percent = 0

    def mark_completed(self):

        self.completed = True

        self.percent = 100

        self.status = "Completed"

    def mark_cancelled(self):

        self.cancelled = True

        self.status = "Cancelled"

    def set_error(self, message: str):

        self.error = message

        self.status = "Error"