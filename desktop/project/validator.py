from pathlib import Path


class ProjectValidator:

    @staticmethod
    def validate(filename):

        return Path(filename).exists()
