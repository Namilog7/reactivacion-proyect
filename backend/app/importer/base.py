"""Capa específica de importación de archivos.

Desacoplada de la lógica de conciliación: un `FileParser` produce
`FilaImportada` normalizadas y la capa de dominio decide qué hacer
con ellas. Permite sumar CSV u otro formato sin tocar la conciliación.
"""

from dataclasses import dataclass


@dataclass
class FilaImportada:
    fila: int
    cliente_numero: str | None
    tipo_archivo: str | None
    tipo_codigo: str | None
    categoria: str | None  # DUPLICADO | INVALIDO | None (pendiente de match)
    mensaje: str | None


class ErrorImportacion(Exception):
    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class FileParser:
    def parse(self, contenido: bytes, tipos_validos: dict) -> list[FilaImportada]:
        raise NotImplementedError