"""Modo demo/sandbox: sesiones de solo lectura respaldadas por Redis.

Los datos reales viven en PostgreSQL; el demo vive únicamente en Redis con
un TTL absoluto por sesión. Este paquete contiene la identidad (principal),
el store de Redis, los datos ficticios, el lector y el servicio que los orquesta.
"""