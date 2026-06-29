from abc import ABC, abstractmethod

class CommandHandler(ABC):
    @abstractmethod
    def handle(self, command): ...

class QueryHandler(ABC):
    @abstractmethod
    def handle(self, query): ...
