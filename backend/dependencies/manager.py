from backend.dependencies.verifier import (
    DependencyVerifier
)


class DependencyManager:

    def __init__(self):

        self.verifier = (
            DependencyVerifier()
        )

    def status(self):

        return self.verifier.verify()