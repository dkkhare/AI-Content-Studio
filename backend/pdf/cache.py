from pathlib import Path


class PDFCache:

    def __init__(self, project_folder):

        self.path = Path(project_folder) / "cache"

        self.path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def thumbnail(self, page):

        return self.path / f"thumb_{page:04d}.png"

    def page_image(self, page):

        return self.path / f"page_{page:04d}.png"