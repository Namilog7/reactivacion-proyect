"""Lector de datos de una sesión de demostración (solo lectura).

Expone las mismas formas de respuesta que los servicios reales, pero
operando sobre el snapshot en Redis y aplicando el alcance por rol del
principal (el operador demo solo ve sus propias gestiones).
"""

from datetime import date

from fastapi import HTTPException, status

from app.sandbox.principal import Principal


class DemoReader:
    def __init__(self, datos: dict, principal: Principal) -> None:
        self.datos = datos
        self.principal = principal

    # --- catálogos ---------------------------------------------------------

    def tipos_operacion(self) -> list[dict]:
        return self.datos["tipos_operacion"]

    def motivos(self) -> list[dict]:
        return self.datos["motivos"]

    def periodos(self) -> list[dict]:
        return sorted(
            self.datos["periodos"], key=lambda p: (-p["anio"], -p["mes"])
        )

    def periodo_vigente(self) -> dict | None:
        return next(
            (p for p in self.datos["periodos"] if p["periodo_vigente"]), None
        )

    def _periodo(self, periodo_id: str) -> dict | None:
        return next((p for p in self.datos["periodos"] if p["id"] == periodo_id), None)

    # --- usuarios (solo supervisor demo) -----------------------------------

    def usuarios(self) -> list[dict]:
        return self.datos["operadores"]

    def get_usuario(self, usuario_id: str) -> dict:
        usuario = next(
            (o for o in self.datos["operadores"] if o["id"] == usuario_id), None
        )
        if usuario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario inexistente.")
        return usuario

    # --- gestiones ---------------------------------------------------------

    def _gestiones_del_operador(self) -> list[dict]:
        return [
            g
            for g in self.datos["gestiones"]
            if g["operador"]["id"] == self.principal.operador_demo_id
        ]

    def gestiones(
        self,
        *,
        periodo_id=None,
        operador_id=None,
        q=None,
        tipo_operacion_id=None,
        pago=None,
        desbloqueado=None,
        tiene_nc=None,
        alerta=None,
        sort="updated_at",
        order="desc",
        page=1,
        page_size=20,
    ) -> dict:
        items = self.datos["gestiones"]
        if self.principal.rol == "OPERADOR":
            operador_id = self.principal.operador_demo_id
        if operador_id:
            items = [g for g in items if g["operador"]["id"] == operador_id]
        if periodo_id:
            items = [g for g in items if g["periodo_id"] == periodo_id]
        if tipo_operacion_id:
            items = [g for g in items if g["tipo_operacion"]["id"] == tipo_operacion_id]
        if q:
            texto = q.strip().lower()
            items = [g for g in items if texto in g["cliente_numero"].lower()]
        if pago is not None:
            items = [g for g in items if g["pago"] == pago]
        if desbloqueado is not None:
            items = [g for g in items if g["desbloqueado"] == desbloqueado]
        if tiene_nc is not None:
            items = [g for g in items if g["tiene_nc"] == tiene_nc]

        total = len(items)

        if alerta == "CRITICA":
            items = [g for g in items if g["alertas"]["nivel"] == "CRITICA"]
        elif alerta == "SI":
            items = [g for g in items if g["alertas"]["nivel"] != "NINGUNA"]

        claves = {
            "cliente_numero": lambda g: g["cliente_numero"],
            "fecha_ofrecida_pago": lambda g: g["fecha_ofrecida_pago"] or "",
            "updated_at": lambda g: g["updated_at"],
        }
        if sort in claves:
            items = sorted(items, key=claves[sort], reverse=(order == "desc"))

        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        inicio = (page - 1) * page_size
        return {
            "items": items[inicio : inicio + page_size],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    def get_gestion(self, gestion_id: str) -> dict:
        gestion = next(
            (g for g in self.datos["gestiones"] if g["id"] == gestion_id), None
        )
        if gestion is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Gestión inexistente.")
        return gestion

    def historial(self, gestion_id: str) -> list[dict]:
        self.get_gestion(gestion_id)
        return self.datos.get("historial", {}).get(gestion_id, [])

    # --- dashboard ---------------------------------------------------------

    def dashboard_operador(self, periodo_id: str | None = None) -> dict:
        periodo = self._periodo(periodo_id) if periodo_id else self.periodo_vigente()
        vacio = {
            "periodo_id": None,
            "periodo_nombre": None,
            "total_gestiones": 0,
            "total_pagos": 0,
            "alertas": 0,
            "criticas": 0,
            "problemas_nc": 0,
            "problemas_desbloqueo": 0,
        }
        if periodo is None:
            return vacio
        gestiones = [
            g
            for g in self._gestiones_del_operador()
            if g["periodo_id"] == periodo["id"]
        ]
        alertas = criticas = problemas_nc = problemas_desbloqueo = 0
        for g in gestiones:
            ev = g["alertas"]
            if ev["nivel"] != "NINGUNA":
                alertas += 1
            if ev["nivel"] == "CRITICA":
                criticas += 1
            if ev["nc_alerta"]:
                problemas_nc += 1
            if ev["desbloqueo_alerta"]:
                problemas_desbloqueo += 1
        return {
            "periodo_id": periodo["id"],
            "periodo_nombre": periodo["nombre"],
            "total_gestiones": len(gestiones),
            "total_pagos": sum(1 for g in gestiones if g["pago"]),
            "alertas": alertas,
            "criticas": criticas,
            "problemas_nc": problemas_nc,
            "problemas_desbloqueo": problemas_desbloqueo,
        }

    def dashboard_supervisor(self) -> dict:
        operadores = self.datos["operadores"]
        resumen_periodos = []
        for p in self.periodos():
            resumen_periodos.append(
                {
                    "id": p["id"],
                    "nombre": p["nombre"],
                    "mes": p["mes"],
                    "anio": p["anio"],
                    "periodo_vigente": p["periodo_vigente"],
                    "total_gestiones": sum(
                        1 for g in self.datos["gestiones"] if g["periodo_id"] == p["id"]
                    ),
                }
            )
        return {
            "total_operadores": len(operadores),
            "operadores_activos": sum(1 for o in operadores if o["activo"]),
            "total_periodos": len(self.datos["periodos"]),
            "total_gestiones": len(self.datos["gestiones"]),
            "periodos": resumen_periodos,
        }

    # --- cargas ------------------------------------------------------------

    def cargas_resumen(self) -> dict:
        vigente = self.periodo_vigente()
        items = []
        for o in self.datos["operadores"]:
            gestiones = (
                [
                    g
                    for g in self.datos["gestiones"]
                    if g["operador"]["id"] == o["id"] and g["periodo_id"] == vigente["id"]
                ]
                if vigente
                else []
            )
            alertas = sum(1 for g in gestiones if g["alertas"]["nivel"] != "NINGUNA")
            criticas = sum(1 for g in gestiones if g["alertas"]["nivel"] == "CRITICA")
            items.append(
                {
                    "id": o["id"],
                    "username": o["username"],
                    "nombre": o["nombre"],
                    "activo": o["activo"],
                    "gestiones": len(gestiones),
                    "pagos": sum(1 for g in gestiones if g["pago"]),
                    "alertas": alertas,
                    "criticas": criticas,
                }
            )
        return {
            "periodo": {"id": vigente["id"], "nombre": vigente["nombre"]}
            if vigente
            else None,
            "items": items,
        }