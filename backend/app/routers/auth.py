from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_usuario
from app.core.security import create_access_token
from app.database import get_db
from app.sandbox.principal import Principal, principal_a_usuario
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(credenciales: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    usuario = AuthService(db).autenticar(credenciales)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos.",
        )
    token = create_access_token(subject=str(usuario.id), rol=usuario.rol)
    return TokenResponse(
        access_token=token,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioOut)
def me(principal: Annotated[Principal, Depends(get_current_usuario)]):
    return UsuarioOut.model_validate(principal_a_usuario(principal))