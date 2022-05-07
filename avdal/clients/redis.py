import redis


class Redis:
    def __init__(self, host, port, pwd, prefix=None):
        self.prefix = prefix
        self.host = host
        self.port = port
        self.client = redis.Redis(host=self.host, port=self.port, password=pwd)

    def set(self, key, value, ttl=None):
        if self.prefix:
            key = self.prefix + key

        self.client.set(key, value, ttl)

    def get(self, key):
        if self.prefix:
            key = self.prefix + key

        return self.client.get(key)
