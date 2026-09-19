from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.security import decode_access_token
from app.database import SessionLocal
from app.domain.enums import Rol
from app.models.usuario import Usuario
from app.sandbox.principal import Principal, TIPO_DEMO, TIPO_REAL
from app.sandbox.store import SandboxStore, obtener_sandbox_store


def get_current_usuario(
    authorization: Annotated[str | None, Header()] = None,
    store: Annotated[SandboxStore, Depends(obtener_sandbox_store)] = None,
) -> Principal:
    """Resuelve el usuario autenticado (real o de demostración).

    Los tokens reales se validan contra PostgreSQL. Los tokens demo se
    validan contra Redis (claims de la sesión). Si Redis no responde,
    las sesiones demo reciben un error controlado 503 y el flujo real
    no se ve afectado.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
        )

    if payload.get("tipo") == TIPO_DEMO:
        sandbox_id = payload.get("sub")
        if not sandbox_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión de demostración inválida.",
            )
        try:
            claims = store.obtener(sandbox_id)
        except RedisConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de demostración no está disponible en este momento.",
            )
        if claims is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sesión de demostración expirada o inválida.",
            )
        return Principal(
            tipo=TIPO_DEMO,
            rol=claims["rol"],
            user_id=sandbox_id,
            sandbox_id=sandbox_id,
            nombre=claims["nombre"],
            username=claims["username"],
            operador_demo_id=claims.get("operador_demo_id"),
            activo=bool(claims.get("activo", True)),
        )

    user_id = payload.get("sub")
    db = SessionLocal()
    try:
        usuario = db.get(Usuario, user_id) if user_id else None
    finally:
        db.close()
    if usuario is None or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inexistente o desactivado.",
        )
    return Principal(
        tipo=TIPO_REAL,
        rol=usuario.rol,
        user_id=str(usuario.id),
        sandbox_id=None,
        nombre=usuario.nombre,
        username=usuario.username,
        activo=usuario.activo,
        created_at=usuario.created_at,
    )


def require_supervisor(
    principal: Annotated[Principal, Depends(get_current_usuario)],
) -> Principal:
    if principal.rol != Rol.SUPERVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de supervisor.",
        )
    return principal