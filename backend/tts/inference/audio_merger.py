from pydub import AudioSegment


class AudioMerger:

    def merge(
        self,
        wav_files,
        output_file,
    ):

        audio = AudioSegment.empty()

        for file in wav_files:

            audio += AudioSegment.from_wav(file)

        audio.export(
            output_file,
            format="wav",
        )

        return output_file