from pathlib import Path


class OCRCache:

    def __init__(self, project):

        self.folder = (
            Path(project)
            / "ocr_cache"
        )

        self.folder.mkdir(
            parents=True,
            exist_ok=True,
        )

    def page_file(self, page):

        return self.folder / f"{page:04d}.txt"