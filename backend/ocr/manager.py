from concurrent.futures import ThreadPoolExecutor


class OCRManager:

    def __init__(self, engine):

        self.engine = engine

    def process_pages(self, pages):

        results = []

        with ThreadPoolExecutor(max_workers=4) as pool:

            futures = []

            for page in pages:

                futures.append(
                    pool.submit(
                        self.engine.recognize,
                        page.image,
                        page.number,
                    )
                )

            for future in futures:

                results.append(
                    future.result()
                )

        return results