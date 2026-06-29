import os

class SecretProvider:
    def get(self, key: str, default: str | None = None) -> str | None:
        return os.getenv(key, default)
