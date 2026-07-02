from __future__ import annotations

import logging


class LoggingProvider:
    def create(self, name: str) -> logging.Logger:
        return logging.getLogger(name)
