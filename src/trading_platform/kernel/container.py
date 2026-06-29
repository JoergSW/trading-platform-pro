class Container:
    def __init__(self):
        self._items={}
    def add(self,key,obj): self._items[key]=obj
    def get(self,key): return self._items[key]
