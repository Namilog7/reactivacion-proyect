"""Carga de archivos por operador (mapa del supervisor)."""

from io import BytesIO

from openpyxl import Workbook

from tests.conftest import auth, crear_gestion


def archivo_clientes(*numeros, encabezado=True) -> dict:
    wb = Workbook()
    ws = wb.active
    if encabezado:
        ws.append(["número de cliente"])
    for n in numeros:
        ws.append([n])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return {"file": (
        "clientes.xlsx",
        buf.read(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )}


def _crear_gestion_op(client, headers, operador, periodo, tipos, cliente, **flags):
    g = crear_gestion(
        client,
        headers,
        cliente=cliente,
        periodo_id=str(periodo.id),
        tipo_id=str(tipos["promesa"].id),
        operador_id=str(operador.id),
        **flags,
    )
    return g


def test_pago_y_desbloqueo_reactivado(client, supervisor, operador, periodo, tipos):
    headers = auth(client, supervisor)
    g = _crear_gestion_op(client, headers, operador, periodo, tipos, "100001")

    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "PAGO_DESBLOQUEO"},
        files=archivo_clientes("100001"),
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["actualizadas"] == 1
    assert body["modificaciones"] == 2

    gestion = client.get(f"/gestiones/{g['id']}", headers=headers).json()
    assert gestion["pago"] is True
    assert gestion["desbloqueado"] is True


def test_pago_sin_desbloqueo_no_toca_desbloqueado(
    client, supervisor, operador, periodo, tipos
):
    headers = auth(client, supervisor)
    g = _crear_gestion_op(client, headers, operador, periodo, tipos, "100002")

    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "PAGO_SIN_DESBLOQUEO"},
        files=archivo_clientes("100002"),
    )
    assert res.status_code == 201, res.text
    gestion = client.get(f"/gestiones/{g['id']}", headers=headers).json()
    assert gestion["pago"] is True
    assert gestion["desbloqueado"] is False
    assert gestion["tiene_nc"] is False


def test_deuda_sin_nc_no_toca_pago(client, supervisor, operador, periodo, tipos):
    headers = auth(client, supervisor)
    g = _crear_gestion_op(
        client, headers, operador, periodo, tipos, "100003", pago=True, tiene_nc=True
    )

    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "DEUDA_SIN_NC"},
        files=archivo_clientes("100003"),
    )
    assert res.status_code == 201, res.text
    gestion = client.get(f"/gestiones/{g['id']}", headers=headers).json()
    assert gestion["tiene_nc"] is False
    assert gestion["pago"] is True
    assert gestion["desbloqueado"] is False


def test_deuda_sin_nc_ni_desbloqueo(client, supervisor, operador, periodo, tipos):
    headers = auth(client, supervisor)
    g = _crear_gestion_op(
        client,
        headers,
        operador,
        periodo,
        tipos,
        "100004",
        pago=True,
        desbloqueado=True,
        tiene_nc=True,
    )

    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "DEUDA_SIN_NC_SIN_DESBLOQUEO"},
        files=archivo_clientes("100004"),
    )
    assert res.status_code == 201, res.text
    gestion = client.get(f"/gestiones/{g['id']}", headers=headers).json()
    assert gestion["tiene_nc"] is False
    assert gestion["desbloqueado"] is False
    assert gestion["pago"] is True


def test_filas_sin_gestion_se_ignoran_y_avisan(
    client, supervisor, operador, periodo, tipos
):
    headers = auth(client, supervisor)
    _crear_gestion_op(client, headers, operador, periodo, tipos, "100005")

    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "PAGO_DESBLOQUEO"},
        files=archivo_clientes("100005", "999999", "100006"),
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["actualizadas"] == 1
    assert body["sin_gestion"] == 2
    assert body["total_filas"] == 3


def test_archivo_sin_encabezado(client, supervisor, operador, periodo, tipos):
    headers = auth(client, supervisor)
    g = _crear_gestion_op(client, headers, operador, periodo, tipos, "100007")

    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "PAGO_DESBLOQUEO"},
        files=archivo_clientes("100007", encabezado=False),
    )
    assert res.status_code == 201, res.text
    gestion = client.get(f"/gestiones/{g['id']}", headers=headers).json()
    assert gestion["pago"] is True


def test_motivo_invalido(client, supervisor, operador):
    headers = auth(client, supervisor)
    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "NO_EXISTE"},
        files=archivo_clientes("100001"),
    )
    assert res.status_code == 400


def test_extension_incorrecta(client, supervisor, operador):
    headers = auth(client, supervisor)
    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "PAGO_DESBLOQUEO"},
        files={"file": ("archivo.csv", b"100001", "text/csv")},
    )
    assert res.status_code == 400


def test_resumen_operadores(client, supervisor, operador, operador2, periodo, tipos):
    headers = auth(client, supervisor)
    _crear_gestion_op(client, headers, operador, periodo, tipos, "100008")
    _crear_gestion_op(client, headers, operador, periodo, tipos, "100009")

    res = client.get("/cargas/resumen", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["periodo"]["id"] == str(periodo.id)
    por_operador = next(i for i in body["items"] if i["id"] == str(operador.id))
    assert por_operador["gestiones"] == 2
    assert por_operador["pagos"] == 0


def test_operador_no_puede_cargar(client, operador):
    headers = auth(client, operador)
    res = client.post(
        "/cargas",
        headers=headers,
        data={"operador_id": str(operador.id), "motivo": "PAGO_DESBLOQUEO"},
        files=archivo_clientes("100001"),
    )
    assert res.status_code == 403