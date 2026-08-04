from dataclasses import dataclass


@dataclass
class NarrationMetadata:

    title: str

    speaker: str

    language: str

    duration: float

    engine: str