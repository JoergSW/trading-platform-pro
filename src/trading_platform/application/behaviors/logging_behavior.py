class LoggingBehavior:
    def invoke(self, request, next_handler):
        return next_handler(request)
