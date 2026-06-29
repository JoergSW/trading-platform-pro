from uuid import uuid4

class IdGenerator:
    def new_id(self):
        return str(uuid4())
