import json

class JsonSerializer:
    def dumps(self,obj):
        return json.dumps(obj)
    def loads(self,text):
        return json.loads(text)
