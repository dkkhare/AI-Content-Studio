import shutil


class FFmpegVerifier:

    @staticmethod
    def exists():

        return shutil.which(
            "ffmpeg"
        ) is not None