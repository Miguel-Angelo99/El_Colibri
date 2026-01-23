from fastapi import FastAPI
from fincas import router as fincas_router
from sectores import router as sectores_router
from revisiones import router as revisiones_router
from trabajadores import router as trabajadores_router
from fastapi import FastAPI, Depends
from auth_simple import require_api_key

app = FastAPI(title="El Colibrí API")

app.include_router(fincas_router)
app.include_router(sectores_router)
app.include_router(revisiones_router)
app.include_router(trabajadores_router)
app = FastAPI(dependencies=[Depends(require_api_key)])

@app.get("/")
def root():
    return {"status": "ok"}


