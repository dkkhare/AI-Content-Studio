from pathlib import Path
import hashlib
import shutil
from urllib.request import urlretrieve

from backend.tts.progress import TTSProgress


class ModelDownloader:
    """
    Generic model downloader.

    Responsibilities
    ----------------
    - Create model directory
    - Check if model exists
    - Download model
    - Verify checksum (optional)
    """

    def __init__(self, model_dir):

        self.model_dir = Path(model_dir)

        self.model_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # --------------------------------------------------
    # Directory
    # --------------------------------------------------

    def directory(self):

        return self.model_dir

    # --------------------------------------------------
    # Exists
    # --------------------------------------------------

    def exists(self, filename):

        return (
            self.model_dir / filename
        ).exists()

    # --------------------------------------------------
    # Download
    # --------------------------------------------------

    def download(

        self,

        url,

        filename,

        callback=None,

    ):

        destination = (
            self.model_dir / filename
        )

        def progress(
            blocks,
            block_size,
            total_size,
        ):

            if total_size <= 0:

                return

            downloaded = blocks * block_size

            percent = min(

                int(

                    downloaded
                    * 100
                    / total_size

                ),

                100,

            )

            if callback:

                callback(

                    TTSProgress(

                        stage="Downloading",

                        current=downloaded,

                        total=total_size,

                        percent=percent,

                    )

                )

        urlretrieve(

            url,

            destination,

            reporthook=progress,

        )

        return destination

    # --------------------------------------------------
    # SHA256
    # --------------------------------------------------

    def verify(

        self,

        filename,

        checksum,

    ):

        path = (
            self.model_dir / filename
        )

        if not path.exists():

            return False

        sha = hashlib.sha256()

        with open(path, "rb") as f:

            while True:

                chunk = f.read(65536)

                if not chunk:

                    break

                sha.update(chunk)

        return sha.hexdigest() == checksum

    # --------------------------------------------------
    # Delete
    # --------------------------------------------------

    def delete(

        self,

        filename,

    ):

        path = (
            self.model_dir / filename
        )

        if path.exists():

            path.unlink()

    # --------------------------------------------------
    # Remove all
    # --------------------------------------------------

    def clear(self):

        if self.model_dir.exists():

            shutil.rmtree(self.model_dir)

            self.model_dir.mkdir(
                parents=True,
                exist_ok=True,
            )