import threading


class RequestMiddleware:

    def __init__(self, get_response, thread_local=threading.local()):
        self.get_response = get_response
        self.thread_local = thread_local

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        self.thread_local.current_request = request
        try:
            return self.get_response(request)
        finally:
            # Don't leak this request into later work on the same thread
            # (BaseModel.save() reads it to stamp creator/updater).
            self.thread_local.current_request = None
