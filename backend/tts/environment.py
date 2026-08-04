import importlib


class TTSEnvironment:

    REQUIRED_MODULES = [
        "torch",
        "soundfile",
        "librosa",
    ]

    def check(self):

        missing = []

        for module in self.REQUIRED_MODULES:

            try:

                importlib.import_module(module)

            except ImportError:

                missing.append(module)

        return missing