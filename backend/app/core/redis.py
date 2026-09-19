"""Cliente Redis compartido de la aplicación.

Un único cliente con pool interno (redis-py) para no abrir conexiones por
request. Se usa exclusivamente para el modo demo/sandbox: los datos reales
viven en PostgreSQL y nunca deben pasar por aquí.
"""

from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.config import settings

_client: Redis | None = None


def get_redis_client() -> Redis:
    """Devuelve el cliente Redis único (lazy). El pool lo administra redis-py."""
    global _client
    if _client is None:
        _client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=3,
        )
    return _client


def redis_disponible() -> bool:
    """Chequeo rápido de disponibilidad (usado para errores controlados)."""
    try:
        return bool(get_redis_client().ping())
    except RedisConnectionError:
        return False