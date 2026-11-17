
import json
from redis.exceptions import RedisError

from extensions import redis_client

TREK_CACHE_KEY = "mad2:available_treks"
TREK_CACHE_TTL = 60


def get_cached_treks():
    try:
        cached = redis_client.get(TREK_CACHE_KEY)

        if cached is not None:
            return json.loads(cached)

    except (RedisError, ValueError, TypeError):
        pass

    return None


def set_cached_treks(treks):
    try:
        redis_client.set(
            TREK_CACHE_KEY,
            json.dumps(treks),
            ex=TREK_CACHE_TTL
        )
    except (RedisError, TypeError, ValueError):
        pass


def invalidate_trek_cache():
    try:
        redis_client.delete(TREK_CACHE_KEY)
    except RedisError:
        pass
