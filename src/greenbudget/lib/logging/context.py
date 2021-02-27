import threading


class Context:
    def __init__(self):
        self.__dict__['_locals'] = threading.local()

    def __getattr__(self, name):
        return getattr(self._locals, name, None)

    def __setattr__(self, name, value):
        setattr(self._locals, name, value)

    def __hasattr__(self, name):
        try:
            return self.__getattr__(name) is not None
        except AttributeError:
            return False
