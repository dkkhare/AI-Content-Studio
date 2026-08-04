from pathlib import Path

from backend.tts.synthesizer import Synthesizer
from backend.narration.merger import NarrationMerger


class NarrationPipeline:

    def __init__(self):

        self.tts = Synthesizer()

        self.merger = NarrationMerger()

    def generate(
        self,
        job,
    ):

        Path(job.output_folder).mkdir(
            parents=True,
            exist_ok=True,
        )

        chunks = self.tts.generate(
            text=job.text,
            voice=job.reference_voice,
            output_folder=job.output_folder,
        )

        output = (
            Path(job.output_folder)
            / "narration.wav"
        )

        return self.merger.merge(
            chunks,
            str(output),
        )