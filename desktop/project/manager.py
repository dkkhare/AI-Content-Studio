from pathlib import Path

from desktop.project.project import Project
from desktop.project.serializer import ProjectSerializer


class ProjectManager:

    def __init__(self):

        self.project = None

        self.filename = None

    def new(self, name, author):

        self.project = Project(
            name=name,
            author=author,
        )

    def save(self):

        if self.project is None:
            return

        if self.filename is None:
            return

        ProjectSerializer.save(
            self.project,
            self.filename,
        )

    def save_as(self, filename):

        self.filename = filename

        self.save()

    def open(self, filename):

        self.filename = filename

        self.project = ProjectSerializer.load(filename)