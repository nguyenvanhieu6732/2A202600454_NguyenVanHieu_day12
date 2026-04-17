import time
import logging
from fastapi import HTTPException
from .storage import storage
from .config import settings

logger = logging.getLogger(__name__)

def check_rate_limit(key: str):
    """
    Sliding window rate limiter using Redis.
    If Redis is not available, falls back to NO rate limiting (with a warning).
    """
    r = storage.get_redis()
    if not r:
        # Fallback logic could be added here, but for production we want Redis.
        # We'll allow request but log warning.
        logger.warning("Rate limiter: Redis not available, skipping limit check.")
        return

    now = time.time()
    pipe = r.pipeline()
    # Key is specific to the user/API key bucket
    redis_key = f"rate_limit:{key}"
    
    # Remove old entries from the sliding window
    pipe.zremrangebyscore(redis_key, 0, now - 60)
    # Add current request
    pipe.zadd(redis_key, {str(now): now})
    # Count requests in the window
    pipe.zcard(redis_key)
    # Set expiry to keep Redis clean
    pipe.expire(redis_key, 61)
    
    _, _, count, _ = pipe.execute()

    if count > settings.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for {key}: {count} requests")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} req/min",
            headers={"Retry-After": "60"},
        )
