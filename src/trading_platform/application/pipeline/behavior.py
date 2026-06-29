from abc import ABC, abstractmethod

class PipelineBehavior(ABC):
    @abstractmethod
    def invoke(self, request, next_handler):
        ...
