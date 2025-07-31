import redis
import os

def with_redis_connection(func):
    def wrapper(*args, **kwargs):
        
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))
        db = int(os.getenv('REDIS_DB', 0))
        password = os.getenv('REDIS_PASSWORD', None)
        
        client = redis.Redis(host=host, port=port, db=db, password=password)
        try:
            return func(client, *args, **kwargs)
        finally:
            client.close()
    return wrapper

class RedisClient:

    @staticmethod
    @with_redis_connection
    def set_key(client, key, value, ex=None):
        """
        设置一个键值对，可选参数ex表示过期时间（秒）
        :param client: Redis客户端实例
        :param key: 键名
        :param value: 值
        :param ex: 过期时间（秒），默认不过期
        :return: 成功返回True，失败返回False
        """
        return client.set(key, value, ex=ex)

    @staticmethod
    @with_redis_connection
    def get_key(client, key):
        """
        获取指定键的值
        :param client: Redis客户端实例
        :param key: 键名
        :return: 如果键存在则返回其对应的值，否则返回None
        """
        return client.get(key)

    @staticmethod
    @with_redis_connection
    def delete_key(client, key):
        """
        删除指定键
        :param client: Redis客户端实例
        :param key: 键名
        :return: 成功删除返回True，键不存在返回False
        """
        return True if client.delete(key) == 1 else False

    @staticmethod
    @with_redis_connection
    def exists(client, key):
        """
        检查键是否存在
        :param client: Redis客户端实例
        :param key: 键名
        :return: 存在返回True，不存在返回False
        """
        return True if client.exists(key) == 1 else False




