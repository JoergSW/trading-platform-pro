from abc import ABC, abstractmethod

class Repository(ABC):
    @abstractmethod
    def add(self, aggregate): ...
    @abstractmethod
    def get(self, identifier): ...
