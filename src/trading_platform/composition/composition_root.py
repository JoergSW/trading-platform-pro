class CompositionRoot:
    def __init__(self):
        self._modules=[]
    def register(self,module):
        self._modules.append(module)
    def build(self,container):
        for module in self._modules:
            module.register(container)
