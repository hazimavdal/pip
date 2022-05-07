import time
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
        value, _ = self.cache.get(key, (None, None))
        self.lock.release()

        return value

    def set(self, key, value, ttl=None):
        exp = None

        if ttl is not None:
            exp = int(time.time()) + ttl

        self.lock.acquire()
        self.cache[key] = (value, exp)
        self.lock.release()

    def incr(self, key, amount=1):
        now = int(time.time())
        self.lock.acquire()

        if key in self.cache:
            self.cache[key] = (self.cache[key][0] + amount, self.cache[key][1])
        else:
            self.cache[key] = (amount, None)

        self.lock.release()

    def cleanup(self):
        self.lock.acquire()

        for key, (_, exp) in list(self.cache.items()):
            if exp and exp < now:
                del self.cache[key]

        self.lock.release()
