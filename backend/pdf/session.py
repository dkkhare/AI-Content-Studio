import json
from pathlib import Path


class PDFSession:

    def __init__(

        self,

        project_folder,

    ):

        self.file = (

            Path(project_folder)

            / "pdf_session.json"

        )

    def save(

        self,

        page,

        zoom,

    ):

        self.file.write_text(

            json.dumps(

                {

                    "page": page,

                    "zoom": zoom,

                },

                indent=4,

            )

        )

    def load(self):

        if not self.file.exists():

            return None

        return json.loads(

            self.file.read_text()

        )