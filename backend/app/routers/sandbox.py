from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.deps import get_current_usuario
from app.core.security import create_access_token
from app.domain.enums import Rol
from app.sandbox.principal import TIPO_DEMO, Principal, principal_a_usuario
from app.sandbox.schemas import DemoLoginRequest
from app.sandbox.service import SandboxService
from app.sandbox.store import SandboxStore, obtener_sandbox_store
from app.schemas.auth import TokenResponse, UsuarioOut
from app.schemas.common import MessageOut

router = APIRouter(prefix="/auth/demo", tags=["auth-demo"])

_PERFILES = {
    Rol.OPERADOR: {
        "username": "demo.opera",
        "nombre": "Operador Demo",
        "operador_demo_id": "demo-op-a",
    },
    Rol.SUPERVISOR: {
        "username": "demo.supervisor",
        "nombre": "Supervisor Demo",
        "operador_demo_id": None,
    },
}


@router.post("/login", response_model=TokenResponse)
def login_demo(
    body: DemoLoginRequest,
    store: Annotated[SandboxStore, Depends(obtener_sandbox_store)] = None,
):
    """Crea una sesión de demostración del rol indicado, sin credenciales."""
    perfil = _PERFILES[body.rol]
    service = SandboxService(store)
    try:
        sandbox_id, _claims = service.crear_sesion(
            rol=body.rol.value,
            username=perfil["username"],
            nombre=perfil["nombre"],
            operador_demo_id=perfil["operador_demo_id"],
        )
    except RedisConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de demostración no está disponible en este momento.",
        )
    token = create_access_token(
        subject=sandbox_id, rol=body.rol.value, tipo=TIPO_DEMO
    )
    principal = Principal(
        tipo=TIPO_DEMO,
        rol=body.rol.value,
        user_id=sandbox_id,
        sandbox_id=sandbox_id,
        nombre=perfil["nombre"],
        username=perfil["username"],
        operador_demo_id=perfil["operador_demo_id"],
    )
    return TokenResponse(
        access_token=token,
        usuario=UsuarioOut.model_validate(principal_a_usuario(principal)),
    )


@router.post("/logout", response_model=MessageOut)
def logout_demo(
    principal: Annotated[Principal, Depends(get_current_usuario)] = None,
    store: Annotated[SandboxStore, Depends(obtener_sandbox_store)] = None,
):
    """Cierra la sesión demo: elimina los claims y los datos en Redis."""
    if principal.es_demo:
        try:
            SandboxService(store).cerrar_sesion(principal.sandbox_id)
        except RedisConnectionError:
            pass  # si Redis está caído la sesión igual expira sola; el cliente limpia su token
    return MessageOut(detalle="ok")