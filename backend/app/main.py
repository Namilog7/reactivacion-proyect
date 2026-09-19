from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    cargas,
    catalogos,
    dashboard,
    gestiones,
    periodos,
    sandbox,
    usuarios,
)

app = FastAPI(
    title="Sistema de Gestión de Cobranzas",
    description="Registro y seguimiento de gestiones de cobranza.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sandbox.router)
app.include_router(usuarios.router)
app.include_router(periodos.router)
app.include_router(catalogos.router)
app.include_router(gestiones.router)
app.include_router(dashboard.router)
app.include_router(cargas.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}