"""Tests de las reglas de alerta (sección 7). No requieren base de datos."""

from app.domain.alertas import evaluar_alertas
from app.domain.enums import NivelAlerta

P = "PROMESA_PAGO"
B = "DEUDA_BONIFICADA"


def test_regla1_pago_sin_nc():
    ev = evaluar_alertas(P, pago=True, tiene_nc=False, desbloqueado=True)
    assert ev["nivel"] == NivelAlerta.ALERTA
    assert ev["nc_alerta"] is True
    assert "Pagó sin nota de crédito" in ev["mensajes"][0]


def test_regla2_pago_sin_desbloqueo():
    ev = evaluar_alertas(P, pago=True, tiene_nc=True, desbloqueado=False)
    assert ev["nivel"] == NivelAlerta.ALERTA
    assert ev["desbloqueo_alerta"] is True
    assert "Pagó sin desbloqueo" in ev["mensajes"][0]


def test_regla3_bonificada_sin_nc():
    ev = evaluar_alertas(B, pago=False, tiene_nc=False, desbloqueado=False)
    assert ev["nivel"] == NivelAlerta.ALERTA
    assert ev["nc_alerta"] is True


def test_regla4_situacion_critica():
    ev = evaluar_alertas(B, pago=True, tiene_nc=False, desbloqueado=True)
    assert ev["nivel"] == NivelAlerta.CRITICA
    assert ev["nc_alerta"] is True
    assert ev["desbloqueo_alerta"] is False
    assert any("crítica" in m.lower() for m in ev["mensajes"])


def test_bonificada_pago_sin_nc_sin_desbloqueo_no_es_critica():
    # Regla 4 exige desbloqueado=True; sin desbloqueo es ALERTA (regla 1) pero no crítica.
    ev = evaluar_alertas(B, pago=True, tiene_nc=False, desbloqueado=False)
    assert ev["nivel"] == NivelAlerta.ALERTA
    assert ev["desbloqueo_alerta"] is True
    assert ev["nivel"] != NivelAlerta.CRITICA


def test_sin_alertas():
    ev = evaluar_alertas(P, pago=True, tiene_nc=True, desbloqueado=True)
    assert ev["nivel"] == NivelAlerta.NINGUNA
    assert ev["nc_alerta"] is False
    assert ev["desbloqueo_alerta"] is False
    assert ev["mensajes"] == []