import importlib


class PackageVerifier:

    @staticmethod
    def installed(package):

        try:

            importlib.import_module(
                package
            )

            return True

        except Exception:

            return False