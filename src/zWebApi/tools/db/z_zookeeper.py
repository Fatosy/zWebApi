from kazoo.client import KazooClient
from contextlib import contextmanager
import os

class ZKSession:
    def __init__(self):
        self.zk_hosts = os.getenv('ZOOKEEPER_HOSTS', '127.0.0.1:2181')
        self.zk = KazooClient(hosts=self.zk_hosts)
        self.lock = None

    def connect(self):
        if not self.zk.connected:
            self.zk.start()

    def disconnect(self):
        if self.zk.connected:
            self.zk.stop()
            self.zk.close()

    @contextmanager
    def acquire_lock(self, path, identifier=None):
        self.connect()
        try:
            self.lock = self.zk.Lock(path, identifier=identifier)
            with self.lock:
                yield
        finally:
            self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()



