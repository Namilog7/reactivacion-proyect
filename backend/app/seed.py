"""Datos de desarrollo (idempotentes).

Crea catálogos base, usuarios, períodos, clientes y gestiones que
ejercitan todas las combinaciones de alertas del dominio.
"""

from datetime import date

from app.core.security import hash_password
from app.database import SessionLocal
from app.domain.enums import Rol
from app.models.catalogos import MotivoConciliacion, TipoOperacion
from app.models.cliente import Cliente
from app.models.gestion import Gestion
from app.models.periodo import Periodo
from app.models.usuario import Usuario
from app.repositories.periodo_repo import PeriodoRepo, TipoOperacionRepo


def _seed_catalogos(db):
    for codigo, nombre in (
        ("PROMESA_PAGO", "Promesa de pago"),
        ("DEUDA_BONIFICADA", "Deuda bonificada"),
    ):
        if TipoOperacionRepo.get_by_codigo(db, codigo) is None:
            db.add(TipoOperacion(codigo=codigo, nombre=nombre))

    for codigo, nombre, descripcion in (
        (
            "PAGOS",
            "Pagos",
            "El archivo representa clientes que pagaron. Se actualiza el estado de pago.",
        ),
        (
            "DEUDAS_SIN_NC",
            "Deudas sin notas de crédito",
            "El archivo representa deudas que aún no tienen nota de crédito. "
            "Se actualiza el estado de notas de crédito.",
        ),
    ):
        if (
            db.query(MotivoConciliacion)
            .filter(MotivoConciliacion.codigo == codigo)
            .first()
            is None
        ):
            db.add(
                MotivoConciliacion(
                    codigo=codigo, nombre=nombre, descripcion=descripcion
                )
            )
    db.commit()


def _seed_usuarios(db):
    credenciales = [
        ("supervisor", "supervisor123", "Supervisor Principal", Rol.SUPERVISOR),
        ("operador1", "operador123", "Operador Uno", Rol.OPERADOR),
        ("operador2", "operador123", "Operador Dos", Rol.OPERADOR),
    ]
    for username, password, nombre, rol in credenciales:
        if db.query(Usuario).filter(Usuario.username == username).first() is None:
            db.add(
                Usuario(
                    username=username,
                    password_hash=hash_password(password),
                    nombre=nombre,
                    rol=rol,
                )
            )
    db.commit()


def _seed_periodos(db):
    periodos = [
        ("Agosto 2026", 8, 2026, False),
        ("Septiembre 2026", 9, 2026, True),
        ("Octubre 2026", 10, 2026, False),
        ("Noviembre 2026", 11, 2026, False),
    ]
    for nombre, mes, anio, vigente in periodos:
        if PeriodoRepo.get_by_mes_anio(db, mes, anio) is None:
            db.add(
                Periodo(
                    nombre=nombre,
                    mes=mes,
                    anio=anio,
                    periodo_vigente=vigente,
                )
            )
    db.commit()
    # Si ningún período quedó vigente (ej.: seed previo), fija Septiembre.
    if PeriodoRepo.get_vigente(db) is None:
        sep = PeriodoRepo.get_by_mes_anio(db, 9, 2026)
        if sep:
            sep.periodo_vigente = True
            db.commit()


def _cliente(db, numero: str, nombre: str) -> Cliente:
    c = db.query(Cliente).filter(Cliente.numero == numero).first()
    if c is None:
        c = Cliente(numero=numero, nombre=nombre)
        db.add(c)
        db.flush()
    return c


def _gestion(
    db,
    cliente,
    operador: Usuario,
    periodo: Periodo,
    tipo_codigo: str,
    *,
    pago=False,
    desbloqueado=False,
    tiene_nc=False,
    fecha_ofrecida=None,
    observaciones="",
):
    tipo = TipoOperacionRepo.get_by_codigo(db, tipo_codigo)
    existente = (
        db.query(Gestion)
        .filter(
            Gestion.cliente_id == cliente.id,
            Gestion.periodo_id == periodo.id,
        )
        .first()
    )
    if existente:
        return existente
    g = Gestion(
        cliente_id=cliente.id,
        operador_id=operador.id,
        periodo_id=periodo.id,
        tipo_operacion_id=tipo.id,
        pago=pago,
        desbloqueado=desbloqueado,
        tiene_nc=tiene_nc,
        fecha_ofrecida_pago=fecha_ofrecida,
        observaciones=observaciones,
    )
    db.add(g)
    return g


def _seed_gestiones(db):
    op1 = db.query(Usuario).filter(Usuario.username == "operador1").first()
    op2 = db.query(Usuario).filter(Usuario.username == "operador2").first()
    sep = PeriodoRepo.get_by_mes_anio(db, 9, 2026)
    oct = PeriodoRepo.get_by_mes_anio(db, 10, 2026)

    if sep is None or oct is None or op1 is None or op2 is None:
        return

    # --- Septiembre 2026 (cubre todas las combinaciones de alertas) ---
    gs = [
        # (numero, nombre, operador, tipo, pago, desbloq, nc, fecha)
        ("100001", "Cliente Uno", op1, "PROMESA_PAGO", False, False, False, None,
         "Sin novedades. Cliente sin estado registrado."),
        ("100002", "Cliente Dos", op1, "DEUDA_BONIFICADA", True, True, False, None,
         "CRÍTICA: pago registrado sin NC."),
        ("100003", "Cliente Tres", op1, "PROMESA_PAGO", True, False, True, date(2026, 9, 15),
         "Regla 2: pagó sin desbloqueo."),
        ("100004", "Cliente Cuatro", op1, "DEUDA_BONIFICADA", False, False, False, None,
         "Regla 3: bonificada sin NC."),
        ("100005", "Cliente Cinco", op1, "PROMESA_PAGO", True, False, False, None,
         "Regla 1 y 2 combinadas."),
        ("100006", "Cliente Seis", op2, "DEUDA_BONIFICADA", True, True, True, date(2026, 9, 20),
         "Todo correcto."),
        ("100007", "Cliente Siete", op2, "PROMESA_PAGO", True, True, True, date(2026, 9, 18),
         "Todo correcto."),
        ("100008", "Cliente Ocho", op2, "PROMESA_PAGO", False, False, False, None, ""),
    ]
    for num, nombre, op, tipo, pago, desb, nc, fecha, obs in gs:
        _gestion(
            db,
            _cliente(db, num, f"Cliente {num}" if nombre == "_" else nombre),
            op,
            sep,
            tipo,
            pago=pago,
            desbloqueado=desb,
            tiene_nc=nc,
            fecha_ofrecida=fecha,
            observaciones=obs,
        )

    # --- Octubre 2026 (mismos clientes, períodos independientes; caso §33) ---
    _gestion(
        db,
        _cliente(db, "100003", "Cliente Tres"),
        op1,
        oct,
        "DEUDA_BONIFICADA",
        pago=False,
        desbloqueado=False,
        tiene_nc=False,
    )
    _gestion(
        db,
        _cliente(db, "100006", "Cliente Seis"),
        op2,
        oct,
        "PROMESA_PAGO",
        pago=False,
        desbloqueado=False,
        tiene_nc=False,
        fecha_ofrecida=date(2026, 10, 5),
    )

    # Clientes existentes sin gestión en Septiembre (para casos de conciliación).
    _cliente(db, "200001", "Cliente Sin Gestión Uno")
    _cliente(db, "200002", "Cliente Sin Gestión Dos")

    db.commit()


def run() -> None:
    db = SessionLocal()
    try:
        _seed_catalogos(db)
        _seed_usuarios(db)
        _seed_periodos(db)
        _seed_gestiones(db)
        print("[seed] OK")
    finally:
        db.close()


if __name__ == "__main__":
    run()