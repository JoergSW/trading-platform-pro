from abc import ABC, abstractmethod

class RepositoryBase(ABC):
    @abstractmethod
    def add(self, entity): ...
    @abstractmethod
    def get(self, identifier): ...
