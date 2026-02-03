import redis
import json
from core.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD # 记得在 config 里配一下

class CacheManager:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            try:
                # 初始化连接池 (生产环境标配)
                pool = redis.ConnectionPool(
                    host=REDIS_HOST or 'localhost',
                    port=REDIS_PORT or 6379,
                    password=REDIS_PASSWORD,
                    decode_responses=True, # 自动转成字符串，不用处理 bytes
                    socket_connect_timeout=1 # 连接超时设短一点，连不上就放弃
                )
                cls._client = redis.Redis(connection_pool=pool)
                # 测试连接
                cls._client.ping()
                print("⚡️ [Cache] Redis 连接成功！")
            except Exception as e:
                print(f"⚠️ [Cache] Redis 连接失败 (将降级为无缓存模式): {e}")
                cls._client = None
        return cls._instance

    def get(self, key: str):
        """安全获取"""
        if not self._client: return None
        try:
            val = self._client.get(key)
            if val:
                print(f"⚡️ [Cache] HIT: {key}")
            return val
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: int = 3600):
        """
        安全写入
        :param ttl: 过期时间 (秒)，默认 1 小时。
                    生产环境一定要设过期时间，防止内存爆满！
        """
        if not self._client: return
        try:
            self._client.setex(key, ttl, value)
        except Exception as e:
            print(f"⚠️ [Cache] Write Failed: {e}")