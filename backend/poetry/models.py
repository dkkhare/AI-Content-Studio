from dataclasses import dataclass, field
from typing import List


@dataclass
class Verse:
    number: int
    text: str


@dataclass
class Stanza:
    number: int
    verses: List[Verse] = field(default_factory=list)


@dataclass
class Poem:
    id: int
    title: str
    language: str
    author: str
    stanzas: List[Stanza] = field(default_factory=list)