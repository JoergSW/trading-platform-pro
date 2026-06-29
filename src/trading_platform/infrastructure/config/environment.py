import os

class Environment:
    @staticmethod
    def profile(default='development'):
        return os.getenv('TP_PROFILE', default)
