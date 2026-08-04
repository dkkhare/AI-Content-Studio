from backend.pdf.progress import PDFProgress


class PDFWorker:

    def process(
        self,
        pdf,
        callback=None,
    ):

        total = len(pdf)

        for i in range(total):

            progress = PDFProgress(
                current_page=i + 1,
                total_pages=total,
                percent=int(
                    ((i + 1) / total) * 100
                ),
                status="Processing",
            )

            if callback:

                callback(progress)