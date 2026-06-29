class ValidationBehavior:
    def __init__(self,*validators):
        self.validators=validators
    def invoke(self, request, next_handler):
        for v in self.validators:
            v.validate(request)
        return next_handler(request)
