"""Configuración de tests.

Crea una base PostgreSQL separada (`cobranzas_test`), la migra con Alembic
y la limpia entre tests. Los tests se ejecutan así:

    docker compose run --rm backend pytest
"""

import os
import uuid as uuid_module
from io import BytesIO

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

TEST_DB = "cobranzas_test"

TABLAS = [
    "historial_cambios",
    "registros_conciliacion",
    "gestiones",
    "conciliaciones",
    "clientes",
    "periodos",
    "usuarios",
    "tipos_operacion",
    "motivos_conciliacion",
]


def _preparar_base() -> None:
    base_url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://cobranzas:cobranzas@db:5432/cobranzas"
    )
    head, _, _db = base_url.rpartition("/")
    test_url = f"{head}/{TEST_DB}"

    admin = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        existe = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB}
        ).scalar()
        if not existe:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB}"'))
    admin.dispose()

    os.environ["DATABASE_URL"] = test_url
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


try:
    _preparar_base()
    DB_DISPONIBLE = True
    _DB_ERROR = None
except Exception as exc:  # sin Postgres disponible (p. ej. en el host) los tests con BD se omiten
    DB_DISPONIBLE = False
    _DB_ERROR = exc

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.domain.enums import Rol  # noqa: E402
from app.models.catalogos import (  # noqa: E402
    MotivoConciliacion,
    TipoOperacion,
)
from app.models.gestion import Gestion  # noqa: E402
from app.models.periodo import Periodo  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402


def _require_db():
    if not DB_DISPONIBLE:
        pytest.skip(f"Base de datos no disponible: {_DB_ERROR}")


@pytest.fixture()
def _limpiar_db():
    _require_db()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE " + ", ".join(TABLAS) + " RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture()
def db(_limpiar_db) -> Session:
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture()
def client(_limpiar_db):
    with TestClient(app) as c:
        yield c


def _usuario(db: Session, username: str, rol: Rol, password: str = "pass123") -> Usuario:
    u = Usuario(
        id=uuid_module.uuid4(),
        username=username,
        password_hash=hash_password(password),
        nombre=f"Nombre {username}",
        rol=rol,
    )
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def supervisor(db):
    return _usuario(db, "sup", Rol.SUPERVISOR)


@pytest.fixture()
def operador(db):
    return _usuario(db, "op1", Rol.OPERADOR)


@pytest.fixture()
def operador2(db):
    return _usuario(db, "op2", Rol.OPERADOR)


@pytest.fixture()
def periodo(db) -> Periodo:
    p = Periodo(
        id=uuid_module.uuid4(),
        nombre="Septiembre 2026",
        mes=9,
        anio=2026,
        periodo_vigente=True,
    )
    db.add(p)
    db.commit()
    return p


@pytest.fixture()
def periodo_oct(db) -> Periodo:
    p = Periodo(
        id=uuid_module.uuid4(),
        nombre="Octubre 2026",
        mes=10,
        anio=2026,
    )
    db.add(p)
    db.commit()
    return p


@pytest.fixture()
def tipos(db) -> dict[str, TipoOperacion]:
    t = {
        "promesa": TipoOperacion(
            id=uuid_module.uuid4(), codigo="PROMESA_PAGO", nombre="Promesa de pago"
        ),
        "bonificada": TipoOperacion(
            id=uuid_module.uuid4(),
            codigo="DEUDA_BONIFICADA",
            nombre="Deuda bonificada",
        ),
    }
    db.add_all(t.values())
    db.commit()
    return t


@pytest.fixture()
def motivos(db) -> dict[str, MotivoConciliacion]:
    m = {
        "pagos": MotivoConciliacion(
            id=uuid_module.uuid4(), codigo="PAGOS", nombre="Pagos"
        ),
        "deudas_sin_nc": MotivoConciliacion(
            id=uuid_module.uuid4(),
            codigo="DEUDAS_SIN_NC",
            nombre="Deudas sin notas de crédito",
        ),
    }
    db.add_all(m.values())
    db.commit()
    return m


def auth(client: TestClient, usuario: Usuario) -> dict:
    res = client.post(
        "/auth/login", json={"username": usuario.username, "password": "pass123"}
    )
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def crear_gestion(
    client: TestClient,
    headers: dict,
    *,
    cliente: str,
    periodo_id: str,
    tipo_id: str,
    operador_id: str | None = None,
    pago=False,
    desbloqueado=False,
    tiene_nc=False,
) -> dict:
    body = {
        "cliente_numero": cliente,
        "periodo_id": periodo_id,
        "tipo_operacion_id": tipo_id,
        "fecha_ofrecida_pago": None,
        "pago": pago,
        "desbloqueado": desbloqueado,
        "tiene_nc": tiene_nc,
        "observaciones": "",
    }
    if operador_id:
        body["operador_id"] = operador_id
    res = client.post("/gestiones", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def archivo_xlsx(filas: list[tuple[str, str]]) -> dict:
    """Genera el .xlsx con las columnas 'número de cliente' y 'tipo de operación'."""
    wb = Workbook()
    ws = wb.active
    ws.append(["número de cliente", "tipo de operación"])
    for numero, tipo in filas:
        ws.append([numero, tipo])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return {
        "file": (
            "clientes.xlsx",
            buf.read(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }