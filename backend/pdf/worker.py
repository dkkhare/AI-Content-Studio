from pathlib import Path
import time

from backend.pdf.progress import PDFProgress
from backend.pdf.statistics import PDFStatistics
from backend.pdf.report import PDFImportReport
from backend.pdf.session import PDFSession

from backend.ocr.pipeline import OCRPipeline
from backend.ocr.exporter import OCRExporter


class PDFWorker:
    """
    Production PDF import worker.

    Responsibilities
    ----------------
    • Iterate through every page
    • Extract embedded text
    • Run OCR when required
    • Save extracted text
    • Save import session
    • Generate statistics
    • Report progress
    • Support cancellation
    """

    def __init__(self):

        self.cancel_requested = False

        self.statistics = PDFStatistics()

        self.ocr = OCRPipeline()

        self.exporter = OCRExporter()

    def cancel(self):

        self.cancel_requested = True

    def process(
        self,
        pdf,
        output_folder=None,
        callback=None,
        session=None,
        start_page=0,
    ):

        total_pages = len(pdf)

        start_time = time.time()

        if output_folder is None:

            output_folder = "output"

        Path(output_folder).mkdir(
            parents=True,
            exist_ok=True,
        )

        if session is None:

            session = PDFSession(output_folder)

        for page_number in range(
            start_page,
            total_pages,
        ):

            if self.cancel_requested:

                break

            page = pdf.load_page(page_number)

            text = page.get_text().strip()

            if text:

                self.statistics.text_pages += 1

            else:

                self.statistics.scanned_pages += 1

                image_file = (
                    Path(output_folder)
                    / f"page_{page_number+1:04d}.png"
                )

                pix = page.get_pixmap()

                pix.save(str(image_file))

                text = self.ocr.process_page(
                    page,
                    str(image_file),
                )

            self.exporter.save(
                page_number + 1,
                text,
                output_folder,
            )

            self.statistics.pages_processed += 1

            session.save(
                page=page_number + 1,
                zoom=1.0,
            )

            progress = PDFProgress(

                current_page=page_number + 1,

                total_pages=total_pages,

                percent=int(
                    ((page_number + 1) / total_pages)
                    * 100
                ),

                status="Importing",
            )

            if callback:

                callback(progress)

        elapsed = time.time() - start_time

        report = PDFImportReport(

            pages=self.statistics.pages_processed,

            text_pages=self.statistics.text_pages,

            scanned_pages=self.statistics.scanned_pages,

            ocr_pages=self.statistics.scanned_pages,

            elapsed_seconds=elapsed,

        )

        return report