"""Dependencias FastAPI específicas del modo demo/sandbox."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.deps import get_current_usuario
from app.sandbox.principal import Principal
from app.sandbox.reader import DemoReader
from app.sandbox.store import SandboxStore, obtener_sandbox_store

MENSAJE_SOLO_LECTURA = (
    "El modo demo es de solo lectura: esta acción no está disponible "
    "en una sesión de demostración."
)


def bloquear_demo(
    principal: Annotated[Principal, Depends(get_current_usuario)] = None,
) -> Principal:
    if principal.es_demo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, MENSAJE_SOLO_LECTURA)
    return principal


def get_reader_demo(
    principal: Annotated[Principal, Depends(get_current_usuario)] = None,
    store: Annotated[SandboxStore, Depends(obtener_sandbox_store)] = None,
) -> DemoReader | None:
    if not principal.es_demo:
        return None
    try:
        datos = store.obtener_datos(principal.sandbox_id)
    except RedisConnectionError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El servicio de demostración no está disponible en este momento.",
        )
    if datos is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Sesión de demostración expirada o inválida."
        )
    return DemoReader(datos, principal)