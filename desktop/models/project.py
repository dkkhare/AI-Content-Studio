from dataclasses import dataclass


@dataclass
class Project:

    name: str

    author: str

    version: str = "1.0"

    pdf: str = ""

    voice: str = ""

    image: str = ""