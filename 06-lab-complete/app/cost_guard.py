import time
import logging
import json
from fastapi import HTTPException
from .storage import storage
from .config import settings

logger = logging.getLogger(__name__)

def check_and_record_cost(input_tokens: int, output_tokens: int):
    """
    Check daily budget and record usage in Redis.
    """
    r = storage.get_redis()
    today = time.strftime("%Y-%m-%d")
    redis_key = f"daily_cost:{today}"

    # Calculate cost (simplified pricing)
    # $0.15 / 1M input, $0.60 / 1M output
    cost = (input_tokens / 1000000) * 0.15 + (output_tokens / 1000000) * 0.60

    if not r:
        logger.warning("Cost guard: Redis not available, using fallback check.")
        return # Skip strict budget check if Redis is down

    # Increment and check
    current_cost = r.get(redis_key)
    current_cost = float(current_cost) if current_cost else 0.0

    if current_cost >= settings.daily_budget_usd:
        logger.error(f"Daily budget exhausted: {current_cost} >= {settings.daily_budget_usd}")
        raise HTTPException(
            status_code=503, 
            detail="Daily budget exhausted. Please try again tomorrow."
        )

    # Record usage
    r.incrbyfloat(redis_key, cost)
    r.expire(redis_key, 86400 * 2) # keep for 2 days
