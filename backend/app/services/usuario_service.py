from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repo import UsuarioRepo
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def listar(self) -> list:
        return UsuarioRepo.list(self.db)

    def get(self, usuario_id: str) -> Usuario:
        usuario = UsuarioRepo.get(self.db, usuario_id)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Operador inexistente.")
        return usuario

    def crear(self, data: UsuarioCreate):
        if UsuarioRepo.get_by_username(self.db, data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El usuario '{data.username}' ya existe.",
            )
        usuario = UsuarioRepo.create(
            self.db,
            username=data.username,
            password_hash=hash_password(data.password),
            nombre=data.nombre,
            rol=data.rol,
        )
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def actualizar(self, usuario_id: str, data: UsuarioUpdate, actor_id: str):
        usuario = UsuarioRepo.get(self.db, usuario_id)
        if usuario is None:
            raise HTTPException(status_code=404, detail="Operador inexistente.")

        if data.nombre is not None:
            usuario.nombre = data.nombre
        if data.rol is not None:
            if str(actor_id) == str(usuario.id) and data.rol != "SUPERVISOR":
                raise HTTPException(
                    status_code=400,
                    detail="No puede quitarse el propio rol de supervisor.",
                )
            usuario.rol = data.rol
        if data.activo is not None:
            if str(actor_id) == str(usuario.id) and data.activo is False:
                raise HTTPException(
                    status_code=400, detail="No puede desactivarse a sí mismo."
                )
            usuario.activo = data.activo
        if data.password:
            usuario.password_hash = hash_password(data.password)

        self.db.commit()
        self.db.refresh(usuario)
        return usuario