from fastapi import FastAPI

from fincas import router as fincas_router
from sectores import router as sectores_router
from trabajadores import router as trabajadores_router
from revisiones import router as revisiones_router

app = FastAPI(title="El Colibri API")

# REGISTRAR ROUTERS
app.include_router(fincas_router)
app.include_router(sectores_router)
app.include_router(trabajadores_router)
app.include_router(revisiones_router)


@app.get("/")
def root():
    return {"status": "ok"}



