from dataclasses import dataclass


@dataclass
class TTSProgress:
    """
    Progress information for narration generation.
    """

    stage: str = ""

    status: str = ""

    current_chunk: int = 0

    total_chunks: int = 0

    current_text: str = ""

    percent: int = 0

    elapsed_seconds: float = 0.0

    remaining_seconds: float = 0.0

    output_file: str = ""

    def update_percent(self):

        if self.total_chunks == 0:

            self.percent = 0

        else:

            self.percent = int(

                self.current_chunk

                * 100

                / self.total_chunks

            )

        return self.percent