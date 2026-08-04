from pathlib import Path


class OCRExporter:

    def save(
        self,
        page,
        text,
        folder,
    ):

        output = (
            Path(folder)
            / f"{page:04d}.txt"
        )

        output.write_text(
            text,
            encoding="utf8",
        )