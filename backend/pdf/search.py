from backend.pdf.search_result import SearchResult


class PDFSearch:

    def search(
        self,
        pages,
        keyword,
    ):

        results = []

        keyword = keyword.lower()

        for page_number, text in enumerate(
            pages,
            start=1,
        ):

            for line_number, line in enumerate(
                text.splitlines(),
                start=1,
            ):

                lower = line.lower()

                position = lower.find(keyword)

                if position >= 0:

                    results.append(

                        SearchResult(

                            page=page_number,

                            line=line_number,

                            start=position,

                            end=position + len(keyword),

                            text=line,

                        )

                    )

        return results