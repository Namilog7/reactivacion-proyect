"""Enumeraciones de dominio. Centralizan los valores fijos del sistema.

Los catálogos extensibles (tipo de operación, motivos de conciliación)
viven como tablas, no aquí.
"""

from enum import Enum


class Rol(str, Enum):
    SUPERVISOR = "SUPERVISOR"
    OPERADOR = "OPERADOR"


class OrigenGestion(str, Enum):
    MANUAL = "MANUAL"
    CONCILIACION = "CONCILIACION"


class EstadoConciliacion(str, Enum):
    PREVISUALIZACION = "PREVISUALIZACION"
    PROCESANDO = "PROCESANDO"
    COMPLETADA = "COMPLETADA"
    ERROR = "ERROR"


class CategoriaRegistro(str, Enum):
    COINCIDENCIA = "COINCIDENCIA"
    CLIENTE_SIN_GESTION = "CLIENTE_SIN_GESTION"
    INCONSISTENTE = "INCONSISTENTE"
    DUPLICADO = "DUPLICADO"
    INVALIDO = "INVALIDO"


class OrigenCambio(str, Enum):
    OPERADOR_MANUAL = "OPERADOR_MANUAL"
    SUPERVISOR_MANUAL = "SUPERVISOR_MANUAL"
    CONCILIACION = "CONCILIACION"


class CampoCambio(str, Enum):
    CREACION = "creacion"
    OPERADOR = "operador"
    TIPO_OPERACION = "tipo_operacion"
    FECHA_OFRECIDA_PAGO = "fecha_ofrecida_pago"
    PAGO = "pago"
    DESBLOQUEADO = "desbloqueado"
    TIENE_NC = "tiene_nc"
    OBSERVACIONES = "observaciones"


class NivelAlerta(str, Enum):
    NINGUNA = "NINGUNA"
    ALERTA = "ALERTA"
    CRITICA = "CRITICA"