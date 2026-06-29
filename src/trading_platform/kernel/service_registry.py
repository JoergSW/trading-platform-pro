class ServiceRegistry:
    def __init__(self):
        self._services={}
    def register(self,name,svc):
        self._services[name]=svc
    def resolve(self,name):
        return self._services[name]
