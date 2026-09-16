"""Escenarios 8, 9, 10, 13 y flujos básicos de autenticación/autorización."""

from tests.conftest import auth, crear_gestion


def test_login_login_fallido_y_me(client, supervisor):
    ok = client.post(
        "/auth/login", json={"username": supervisor.username, "password": "pass123"}
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    mal = client.post(
        "/auth/login", json={"username": supervisor.username, "password": "incorrecta"}
    )
    assert mal.status_code == 401

    headers = auth(client, supervisor)
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == supervisor.username


def test_proteccion_endpoints(client):
    assert client.get("/gestiones").status_code == 401
    assert client.get("/periodos").status_code == 401


def test_operador_no_puede_rol_supervisor(client, operador):
    headers = auth(client, operador)
    assert client.get("/usuarios", headers=headers).status_code == 403
    res = client.post(
        "/usuarios",
        headers=headers,
        json={"username": "x", "password": "123456", "nombre": "X"},
    )
    assert res.status_code == 403


def test_supervisor_crud_operadores(client, supervisor):
    headers = auth(client, supervisor)
    res = client.post(
        "/usuarios",
        headers=headers,
        json={"username": "nuevoop", "password": "123456", "nombre": "Nuevo"},
    )
    assert res.status_code == 201
    uid = res.json()["id"]
    patch = client.patch(f"/usuarios/{uid}", headers=headers, json={"activo": False})
    assert patch.status_code == 200
    assert patch.json()["activo"] is False


def test_escenario8_no_dos_gestiones_mismo_cliente_mismo_periodo(
    client, operador, periodo, tipos
):
    headers = auth(client, operador)
    crear_gestion(
        client, headers, cliente="123456", periodo_id=str(periodo.id),
        tipo_id=str(tipos["promesa"].id), operador_id=str(operador.id),
    )
    res = client.post(
        "/gestiones",
        headers=headers,
        json={
            "cliente_numero": "123456",
            "periodo_id": str(periodo.id),
            "tipo_operacion_id": str(tipos["promesa"].id),
        },
    )
    assert res.status_code == 409


def test_escenario9_mismo_cliente_periodos_diferentes(
    client, operador, periodo, periodo_oct, tipos
):
    headers = auth(client, operador)
    g1 = crear_gestion(
        client, headers, cliente="789123", periodo_id=str(periodo.id),
        tipo_id=str(tipos["bonificada"].id),
    )
    g2 = crear_gestion(
        client, headers, cliente="789123", periodo_id=str(periodo_oct.id),
        tipo_id=str(tipos["promesa"].id),
    )
    assert g1["id"] != g2["id"]
    assert g1["tipo_operacion"]["codigo"] == "DEUDA_BONIFICADA"
    assert g2["tipo_operacion"]["codigo"] == "PROMESA_PAGO"


def test_escenario10_cambio_tipo_no_crea_segunda_gestion(
    client, operador, periodo, tipos
):
    headers = auth(client, operador)
    g = crear_gestion(
        client, headers, cliente="123456", periodo_id=str(periodo.id),
        tipo_id=str(tipos["promesa"].id),
    )
    res = client.patch(
        f"/gestiones/{g['id']}",
        headers=headers,
        json={"tipo_operacion_id": str(tipos["bonificada"].id)},
    )
    assert res.status_code == 200
    assert res.json()["id"] == g["id"]
    assert res.json()["tipo_operacion"]["codigo"] == "DEUDA_BONIFICADA"

    # Solo una gestión para el cliente en el período.
    lista = client.get(
        "/gestiones",
        headers=headers,
        params={"periodo_id": str(periodo.id), "q": "123456"},
    )
    assert lista.json()["total"] == 1

    # El cambio queda auditado.
    hist = client.get(f"/gestiones/{g['id']}/historial", headers=headers)
    campos = [h["campo"] for h in hist.json()]
    assert "tipo_operacion" in campos
    assert hist.json()[0]["origen"] == "OPERADOR_MANUAL"


def test_escenario13_operador_no_accede_a_gestion_ajena(
    client, operador, operador2, periodo, tipos
):
    h1 = auth(client, operador)
    h2 = auth(client, operador2)
    g = crear_gestion(
        client, h1, cliente="123456", periodo_id=str(periodo.id),
        tipo_id=str(tipos["promesa"].id), operador_id=str(operador.id),
    )
    # operador2 no puede modificar la gestión de operador1
    res = client.patch(
        f"/gestiones/{g['id']}", headers=h2, json={"pago": True}
    )
    assert res.status_code == 403
    # ni consultarla
    assert client.get(f"/gestiones/{g['id']}", headers=h2).status_code == 403
    # ni verla en su listado
    lista = client.get("/gestiones", headers=h2)
    ids = [i["id"] for i in lista.json()["items"]]
    assert g["id"] not in ids

    # el dueño sí puede
    res = client.patch(f"/gestiones/{g['id']}", headers=h1, json={"pago": True})
    assert res.status_code == 200
    assert res.json()["pago"] is True