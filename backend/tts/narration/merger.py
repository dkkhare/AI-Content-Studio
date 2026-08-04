from pathlib import Path
from pydub import AudioSegment


class NarrationMerger:

    def merge(
        self,
        chunk_files,
        output_file,
    ):

        audio = AudioSegment.empty()

        for file in chunk_files:

            audio += AudioSegment.from_wav(file)

        Path(output_file).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        audio.export(
            output_file,
            format="wav",
        )

        return output_file