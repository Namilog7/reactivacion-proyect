from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario


class UsuarioRepo:
    @staticmethod
    def get(db: Session, usuario_id: str) -> Usuario | None:
        return db.get(Usuario, usuario_id)

    @staticmethod
    def get_by_username(db: Session, username: str) -> Usuario | None:
        return db.scalar(select(Usuario).where(Usuario.username == username))

    @staticmethod
    def list(db: Session) -> list[Usuario]:
        return list(
            db.scalars(select(Usuario).order_by(Usuario.nombre, Usuario.username))
        )

    @staticmethod
    def create(
        db: Session,
        username: str,
        password_hash: str,
        nombre: str,
        rol: str,
    ) -> Usuario:
        u = Usuario(username=username, password_hash=password_hash, nombre=nombre, rol=rol)
        db.add(u)
        db.flush()
        return u