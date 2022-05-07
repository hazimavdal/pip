import threading
from . import Cache


class MemoryCache(Cache):
    def __init__(self, autocleanup=True):
        self.cache = {}
        self.lock = threading.RLock()

        if autocleanup:
            self.cleanup_thread = threading.Thread(target=self.cleanup)
            self.cleanup_thread.start()

    def get(self, key):
        self.lock.acquire()
        value = self.cache.get(key)
        self.lock.release()

        return value

    def set(self, key, value, ttl=None):
        self.lock.acquire()
        self.cache[key] = (value, ttl)
        self.lock.release()

    def incr(self, key, amount=1):
        self.lock.acquire()

        if key in self.cache:
            self.cache[key] = (self.cache[key][0] + amount, self.cache[key][1])
        else:
            self.cache[key] = (amount, None)

        self.lock.release()

    def cleanup(self):
        self.lock.acquire()

        for key in list(self.cache.keys()):
            if self.cache[key][1] is not None and self.cache[key][1] < 0:
                del self.cache[key]

        self.lock.release()
