"""Caso de uso: creación y cierre de sesiones de demostración.

Cada sesión genera un `sandbox_id` único, guarda los claims del usuario y
un snapshot de datos ficticios en Redis con el TTL absoluto configurado.
"""

import uuid

from app.sandbox.seed import construir_datos_demo
from app.sandbox.store import SandboxStore


class SandboxService:
    def __init__(self, store: SandboxStore) -> None:
        self._store = store

    def crear_sesion(
        self,
        *,
        rol: str,
        username: str,
        nombre: str,
        operador_demo_id: str | None = None,
    ) -> tuple[str, dict]:
        sandbox_id = uuid.uuid4().hex
        claims = self._store.crear(
            sandbox_id,
            rol=rol,
            username=username,
            nombre=nombre,
            operador_demo_id=operador_demo_id,
        )
        self._store.guardar_datos(sandbox_id, construir_datos_demo())
        return sandbox_id, claims

    def cerrar_sesion(self, sandbox_id: str) -> None:
        self._store.eliminar(sandbox_id)

    def obtener(self, sandbox_id: str) -> dict | None:
        return self._store.obtener(sandbox_id)