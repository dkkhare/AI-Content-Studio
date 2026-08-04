class OCRScheduler:

    def process(
        self,
        pages,
        callback=None,
    ):

        total = len(pages)

        for index, page in enumerate(pages):

            if callback:

                callback(
                    index + 1,
                    total,
                )