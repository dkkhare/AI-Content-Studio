from dataclasses import dataclass


@dataclass
class SearchResult:

    page: int

    line: int

    start: int

    end: int

    text: str