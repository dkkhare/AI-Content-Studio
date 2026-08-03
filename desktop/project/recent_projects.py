import json
from pathlib import Path

FILE = Path.home() / ".aics_recent.json"


class RecentProjects:

    def __init__(self):

        self.projects = []

        self.load()

    def add(self, filename):

        if filename in self.projects:
            self.projects.remove(filename)

        self.projects.insert(0, filename)

        self.projects = self.projects[:10]

        self.save()

    def save(self):

        with open(FILE, "w") as f:

            json.dump(self.projects, f)

    def load(self):

        if FILE.exists():

            with open(FILE) as f:

                self.projects = json.load(f)