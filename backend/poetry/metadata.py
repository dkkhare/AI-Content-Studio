from dataclasses import dataclass, field
from typing import List


@dataclass
class BookMetadata:
    title: str = ""
    author: str = ""
    language: str = ""
    total_pages: int = 0
    total_poems: int = 0
    estimated_duration: int = 0


@dataclass
class Episode:
    number: int
    title: str
    duration_seconds: int
    poem_ids: List[int] = field(default_factory=list)