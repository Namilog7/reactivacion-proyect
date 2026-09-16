from app.core.security import verify_password
from app.repositories.usuario_repo import UsuarioRepo
from app.schemas.auth import LoginRequest


class AuthService:
    def __init__(self, db) -> None:
        self.db = db

    def autenticar(self, credenciales: LoginRequest):
        usuario = UsuarioRepo.get_by_username(self.db, credenciales.username)
        if usuario is None or not usuario.activo:
            return None
        if not verify_password(credenciales.password, usuario.password_hash):
            return None
        return usuario