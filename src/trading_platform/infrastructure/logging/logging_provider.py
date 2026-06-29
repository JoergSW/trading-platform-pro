import logging

class LoggingProvider:
    def create(self, name:str):
        return logging.getLogger(name)
