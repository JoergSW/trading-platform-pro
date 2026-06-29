class PluginManager:
    def __init__(self):
        self._plugins={}
    def register(self,name,plugin):
        self._plugins[name]=plugin
    def get(self,name):
        return self._plugins[name]
    def all(self):
        return dict(self._plugins)
