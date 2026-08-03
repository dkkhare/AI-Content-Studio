import json

from dataclasses import asdict

from desktop.project.project import Project


class ProjectSerializer:

    @staticmethod
    def save(project: Project, filename: str):

        with open(filename, "w", encoding="utf8") as f:

            json.dump(
                asdict(project),
                f,
                indent=4,
                ensure_ascii=False,
            )

    @staticmethod
    def load(filename: str):

        with open(filename, encoding="utf8") as f:

            data = json.load(f)

        return Project(**data)