from pathlib import Path


class RuntimeValidator:

    @staticmethod
    def validate_reference(reference):

        if not Path(reference).exists():

            raise FileNotFoundError(reference)