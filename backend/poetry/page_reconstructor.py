class PageReconstructor:
    """
    Rejoins text broken by page boundaries.
    """

    def reconstruct(self, pages):

        output = []

        for page in pages:

            output.append(page.text.strip())

        return "\n".join(output)