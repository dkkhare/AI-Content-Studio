from backend.tts.segmenter import TextSegmenter
from backend.tts.providers.f5tts_runtime import (
    F5TTSRuntime,
)


class Synthesizer:

    def __init__(self):

        self.runtime = F5TTSRuntime()

        self.segmenter = TextSegmenter()

    def generate(
        self,
        text,
        voice,
        output_folder,
    ):

        self.runtime.initialize()

        chunks = self.segmenter.split(text)

        outputs = []

        for index, chunk in enumerate(chunks):

            filename = (
                f"{output_folder}/chunk_{index:03d}.wav"
            )

            outputs.append(

                self.runtime.synthesize(
                    chunk,
                    voice,
                    filename,
                )

            )

        return outputs