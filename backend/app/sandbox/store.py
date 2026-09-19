"""Acceso a Redis para las sesiones de demostración (sandbox).

Cada sesión demo guarda dos claves con el mismo TTL absoluto:
- `sandbox:{id}` -> claims del usuario (se validan en cada request).
- `demo:{id}`    -> snapshot de datos ficticios de esa sesión.

El TTL se fija al crear la clave y nunca se renueva: no es deslizante.
El store es inyectable a través de `obtener_sandbox_store` para poder
reemplazarlo en los tests (fakeredis) sin tocar la aplicación.
"""

import json
from datetime import datetime, timezone

from app.config import settings
from app.core.redis import get_redis_client


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SandboxStore:
    def __init__(self, client, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    def _clave_sesion(self, sandbox_id: str) -> str:
        return f"sandbox:{sandbox_id}"

    def _clave_datos(self, sandbox_id: str) -> str:
        return f"demo:{sandbox_id}"

    def crear(
        self,
        sandbox_id: str,
        *,
        rol: str,
        nombre: str,
        username: str,
        operador_demo_id: str | None = None,
    ) -> dict:
        clave = self._clave_sesion(sandbox_id)
        claims = {
            "tipo": "DEMO",
            "rol": rol,
            "nombre": nombre,
            "username": username,
            "operador_demo_id": operador_demo_id,
            "activo": True,
            "created_at": _ahora_iso(),
        }
        self._client.set(clave, json.dumps(claims, ensure_ascii=False), ex=self._ttl)
        return claims

    def guardar_datos(self, sandbox_id: str, datos: dict) -> None:
        self._client.set(
            self._clave_datos(sandbox_id),
            json.dumps(datos, ensure_ascii=False),
            ex=self._ttl,
        )

    def obtener(self, sandbox_id: str) -> dict | None:
        raw = self._client.get(self._clave_sesion(sandbox_id))
        if raw is None:
            return None
        try:
            claims = json.loads(raw)
        except (TypeError, ValueError):
            return None
        if claims.get("activo") is not True:
            return None
        return claims

    def obtener_datos(self, sandbox_id: str) -> dict | None:
        raw = self._client.get(self._clave_datos(sandbox_id))
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    def eliminar(self, sandbox_id: str) -> None:
        self._client.delete(self._clave_sesion(sandbox_id), self._clave_datos(sandbox_id))


_store: SandboxStore | None = None


def obtener_sandbox_store() -> SandboxStore:
    global _store
    if _store is None:
        _store = SandboxStore(get_redis_client(), settings.sandbox_ttl_seconds)
    return _store