import json
from pathlib import Path


class ResumeState:

    def __init__(
        self,
        filename,
    ):

        self.file = Path(filename)

    def save(
        self,
        completed_chunk,
    ):

        self.file.write_text(
            json.dumps(
                {
                    "completed": completed_chunk
                }
            )
        )

    def load(self):

        if not self.file.exists():

            return 0

        return json.loads(
            self.file.read_text()
        )["completed"]