from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.cliente import Cliente


class ClienteRepo:
    @staticmethod
    def get(db: Session, cliente_id: str) -> Cliente | None:
        return db.get(Cliente, cliente_id)

    @staticmethod
    def get_by_numero(db: Session, numero: str) -> Cliente | None:
        return db.scalar(select(Cliente).where(Cliente.numero == numero))

    @staticmethod
    def get_or_create(db: Session, numero: str, nombre: str | None = None) -> Cliente:
        cliente = ClienteRepo.get_by_numero(db, numero)
        if cliente is None:
            cliente = Cliente(numero=numero, nombre=nombre)
            db.add(cliente)
            db.flush()
        elif nombre and not cliente.nombre:
            cliente.nombre = nombre
        return cliente