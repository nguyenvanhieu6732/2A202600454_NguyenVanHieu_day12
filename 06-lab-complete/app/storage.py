import redis
import logging
from .config import settings

logger = logging.getLogger(__name__)

class Storage:
    def __init__(self):
        self.redis = None
        self.use_redis = False
        try:
            if settings.redis_url:
                self.redis = redis.from_url(settings.redis_url, decode_responses=True)
                self.redis.ping()
                self.use_redis = True
                logger.info("✅ Connected to Redis")
            else:
                logger.warning("⚠️ REDIS_URL not set — falling back to in-memory (not for production!)")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.use_redis = False

    def get_redis(self):
        return self.redis if self.use_redis else None

storage = Storage()
