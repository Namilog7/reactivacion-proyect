"""Tests del modo demo/sandbox.

Los tests de sandbox usan `fakeredis` y un TestClient propio: NO dependen
de PostgreSQL. Solo los tests que verifican que el flujo real sigue
funcionando con Redis caído requieren base de datos (se omiten si no hay).
"""

import time

import pytest
from fakeredis import FakeRedis
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from app.domain.enums import Rol
from app.main import app
from app.sandbox.store import SandboxStore, obtener_sandbox_store
from tests import conftest as _conftest


class StoreRoto(SandboxStore):
    def __init__(self) -> None:
        super().__init__(object(), ttl_seconds=1)

    def _caido(self, *_args, **_kwargs):
        raise RedisConnectionError("redis caído")

    ping = _caido
    crear = _caido
    guardar_datos = _caido
    obtener = _caido
    obtener_datos = _caido
    eliminar = _caido


@pytest.fixture()
def redis_fake() -> FakeRedis:
    return FakeRedis(decode_responses=True)


@pytest.fixture()
def store(redis_fake: FakeRedis) -> SandboxStore:
    return SandboxStore(redis_fake, ttl_seconds=3600)


@pytest.fixture()
def san_client(store: SandboxStore):
    app.dependency_overrides[obtener_sandbox_store] = lambda: store
    try:
        with TestClient(app) as c:
            yield c, store
    finally:
        app.dependency_overrides.clear()


def _login(c: TestClient, rol: str) -> dict:
    res = c.post("/auth/demo/login", json={"rol": rol})
    assert res.status_code == 200, res.text
    return res.json()


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- login e identidad -----------------------------------------------------


def test_login_demo_operador(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    assert body["token_type"] == "bearer"
    usuario = body["usuario"]
    assert usuario["tipo"] == "DEMO"
    assert usuario["rol"] == "OPERADOR"
    assert usuario["username"] == "demo.opera"


def test_login_demo_supervisor(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    assert body["usuario"]["rol"] == "SUPERVISOR"
    assert body["usuario"]["tipo"] == "DEMO"


def test_me_demo(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    res = c.get("/auth/me", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    assert res.json()["tipo"] == "DEMO"


def test_login_sin_redis_503(redis_fake):
    app.dependency_overrides[obtener_sandbox_store] = lambda: StoreRoto()
    try:
        with TestClient(app) as c:
            res = c.post("/auth/demo/login", json={"rol": "OPERADOR"})
            assert res.status_code == 503
    finally:
        app.dependency_overrides.clear()


# --- sesión expirada / TTL absoluto ---------------------------------------


def test_sesion_expirada_da_401(san_client):
    c, store = san_client
    body = _login(c, "OPERADOR")
    token = body["access_token"]
    assert c.get("/auth/me", headers=_bearer(token)).status_code == 200
    sandbox_id = body["usuario"]["id"]
    store.eliminar(sandbox_id)
    res = c.get("/auth/me", headers=_bearer(token))
    assert res.status_code == 401


def test_ttl_absoluto_no_se_renueva(redis_fake):
    store = SandboxStore(redis_fake, ttl_seconds=3600)
    app.dependency_overrides[obtener_sandbox_store] = lambda: store
    try:
        with TestClient(app) as c:
            body = _login(c, "OPERADOR")
            sandbox_id = body["usuario"]["id"]
            clave = f"sandbox:{sandbox_id}"
            ttl_inicial = redis_fake.ttl(clave)
            assert 0 < ttl_inicial <= 3600
            c.get("/auth/me", headers=_bearer(body["access_token"]))
            time.sleep(1.05)
            c.get("/auth/me", headers=_bearer(body["access_token"]))
            ttl_final = redis_fake.ttl(clave)
            assert 0 < ttl_final < ttl_inicial  # nunca volvió a 3600
    finally:
        app.dependency_overrides.clear()


def test_sesion_expira_por_ttl(redis_fake):
    store = SandboxStore(redis_fake, ttl_seconds=1)
    app.dependency_overrides[obtener_sandbox_store] = lambda: store
    try:
        with TestClient(app) as c:
            body = _login(c, "SUPERVISOR")
            time.sleep(1.3)
            res = c.get("/auth/me", headers=_bearer(body["access_token"]))
            assert res.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_logout_elimina_sesion(san_client):
    c, store = san_client
    body = _login(c, "OPERADOR")
    token = body["access_token"]
    sandbox_id = body["usuario"]["id"]
    assert store.obtener(sandbox_id) is not None
    res = c.post("/auth/demo/logout", headers=_bearer(token))
    assert res.status_code == 200
    assert store.obtener(sandbox_id) is None


# --- lecturas demo ---------------------------------------------------------


def test_periodos_demo(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.get("/periodos", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    periodos = res.json()
    assert len(periodos) == 4
    vigente = next(p for p in periodos if p["periodo_vigente"])
    assert vigente["id"] == "demo-p-sep"


def test_periodo_vigente_demo(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    res = c.get("/periodos/vigente", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    assert res.json()["id"] == "demo-p-sep"


def test_catalogos_demo(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    tipos = c.get("/tipos-operacion", headers=_bearer(body["access_token"]))
    motivos = c.get("/motivos-conciliacion", headers=_bearer(body["access_token"]))
    assert tipos.status_code == 200 and len(tipos.json()) == 2
    assert motivos.status_code == 200 and len(motivos.json()) == 2


def test_gestiones_operador_solo_ve_las_suyas(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    res = c.get("/gestiones", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 6  # demo-op-a: 6 de 11
    assert all(g["operador"]["id"] == "demo-op-a" for g in data["items"])


def test_gestiones_supervisor_ve_todas(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.get("/gestiones", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    assert res.json()["total"] == 11


def test_gestiones_filtros_y_alertas(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.get(
        "/gestiones",
        params={"alerta": "CRITICA"},
        headers=_bearer(body["access_token"]),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 11  # el total no filtra por alertas (como el real)
    assert all(g["alertas"]["nivel"] == "CRITICA" for g in data["items"])
    res = c.get(
        "/gestiones",
        params={"q": "900002"},
        headers=_bearer(body["access_token"]),
    )
    assert res.json()["total"] == 2  # g-2 (sep) y g-11 (oct)


def test_gestion_detail_e_historial(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    detalle = c.get("/gestiones/demo-g-2", headers=_bearer(body["access_token"]))
    assert detalle.status_code == 200
    assert detalle.json()["alertas"]["nivel"] == "CRITICA"
    hist = c.get(
        "/gestiones/demo-g-2/historial", headers=_bearer(body["access_token"])
    )
    assert hist.status_code == 200
    assert len(hist.json()) == 3


def test_dashboard_operador_demo(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    res = c.get(
        "/dashboard/operador", headers=_bearer(body["access_token"])
    )
    assert res.status_code == 200
    data = res.json()
    assert data["periodo_nombre"] == "Septiembre 2026"
    assert data["total_gestiones"] == 5  # demo-op-a en septiembre


def test_dashboard_supervisor_demo(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.get("/dashboard/supervisor", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    data = res.json()
    assert data["total_operadores"] == 2
    assert data["total_periodos"] == 4
    assert data["total_gestiones"] == 11


def test_cargas_resumen_demo(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.get("/cargas/resumen", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    data = res.json()
    assert data["periodo"]["id"] == "demo-p-sep"
    assert data["items"][0]["gestiones"] == 5


def test_usuarios_demo(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.get("/usuarios", headers=_bearer(body["access_token"]))
    assert res.status_code == 200
    nombres = {u["username"] for u in res.json()}
    assert nombres == {"demo.opera", "demo.operaB"}


# --- modo demo es de solo lectura en el BACKEND ----------------------------


@pytest.mark.parametrize(
    "metodo, ruta, cuerpo",
    [
        ("POST", "/gestiones", {"cliente_numero": "900099", "periodo_id": "demo-p-sep", "tipo_operacion_id": "demo-to-promesa"}),
        ("PATCH", "/gestiones/demo-g-1", {"pago": True}),
        ("POST", "/periodos", {"nombre": "Diciembre 2026", "mes": 12, "anio": 2026}),
        ("PATCH", "/periodos/demo-p-vigente", {"periodo_vigente": True}),
        ("POST", "/usuarios", {"username": "nuevo", "password": "pass123", "nombre": "Nuevo"}),
        ("PATCH", "/usuarios/demo-op-a", {"nombre": "Otro"}),
        ("DELETE", "/usuarios/demo-op-a", None),
    ],
)
def test_escrituras_demo_bloqueadas(san_client, metodo, ruta, cuerpo):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    kwargs = {}
    if cuerpo is not None:
        kwargs["json"] = cuerpo
    res = c.request(metodo, ruta, headers=_bearer(body["access_token"]), **kwargs)
    assert res.status_code == 403
    assert "solo lectura" in res.json()["detail"].lower()


def test_carga_archivo_demo_bloqueada(san_client):
    c, _ = san_client
    body = _login(c, "SUPERVISOR")
    res = c.post(
        "/cargas",
        data={"operador_id": "demo-op-a", "motivo": "PAGO_DESBLOQUEO"},
        files={"file": ("clientes.xlsx", b"", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=_bearer(body["access_token"]),
    )
    assert res.status_code == 403


def test_operador_demo_no_accede_a_gestiones_ajenas(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    res = c.get("/gestiones/demo-g-6", headers=_bearer(body["access_token"]))
    assert res.status_code == 403


def test_operador_demo_no_lista_usuarios(san_client):
    c, _ = san_client
    body = _login(c, "OPERADOR")
    res = c.get("/usuarios", headers=_bearer(body["access_token"]))
    assert res.status_code == 403


# --- aislamiento entre sesiones demo --------------------------------------


def test_aislamiento_entre_sesiones(san_client):
    c, _ = san_client
    op = _login(c, "OPERADOR")
    sup = _login(c, "SUPERVISOR")
    assert op["usuario"]["id"] != sup["usuario"]["id"]
    op_g = c.get("/gestiones", headers=_bearer(op["access_token"])).json()
    sup_g = c.get("/gestiones", headers=_bearer(sup["access_token"])).json()
    assert op_g["total"] == 6
    assert sup_g["total"] == 11


# --- el flujo real no depende de Redis -------------------------------------


@pytest.mark.skipif(
    not _conftest.DB_DISPONIBLE, reason="PostgreSQL no disponible"
)
def test_real_no_se_ve_afectado_por_redis_caido(client, operador):
    app.dependency_overrides[obtener_sandbox_store] = lambda: StoreRoto()
    try:
        token = client.post(
            "/auth/login",
            json={"username": operador.username, "password": "pass123"},
        )
        assert token.status_code == 200, token.text
        headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
        res = client.get("/gestiones", headers=headers)
        assert res.status_code == 200
        assert res.json()["total"] == 0
        res = client.get("/periodos", headers=headers)
        assert res.status_code == 200
    finally:
        app.dependency_overrides.clear()