from pydub import AudioSegment


class AudioProcessor:

    def normalize(self, filename):

        audio = AudioSegment.from_file(filename)

        audio = audio.normalize()

        audio.export(filename, format="wav")

        return filename

    def trim_silence(self, filename):

        # Placeholder

        return filename