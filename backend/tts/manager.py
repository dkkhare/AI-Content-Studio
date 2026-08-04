from backend.tts.provider_registry import ProviderRegistry


class TTSManager:

    def __init__(self):

        self.registry = ProviderRegistry()

    def register(self, provider):

        self.registry.register(provider)

    def provider(self, name):

        return self.registry.get(name)