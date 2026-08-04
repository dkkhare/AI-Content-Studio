from dataclasses import dataclass


@dataclass
class TTSProgress:

    current_chunk: int = 0

    total_chunks: int = 0

    current_text: str = ""

    percent: int = 0