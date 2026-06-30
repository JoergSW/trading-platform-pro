from __future__ import annotations

import os


class Environment:
    @staticmethod
    def profile(default: str = "development") -> str:
        value = os.getenv("TP_PROFILE", default)
        return value.strip() or default
