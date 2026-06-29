from .result import Result

class ResultFactory:
    @staticmethod
    def ok(value=None):
        return Result(success=True, value=value)

    @staticmethod
    def fail(error:str):
        return Result(success=False, error=error)
