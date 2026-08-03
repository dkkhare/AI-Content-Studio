"""
AI Content Studio Project Model
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Project:

    name: str

    author: str

    description: str = ""

    pdf: str = ""

    voice: str = ""

    avatar: str = ""

    output_folder: str = "output"

    theme: str = "Classic"

    language: str = "English"

    videos: List[str] = field(default_factory=list)