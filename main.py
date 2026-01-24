from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from fincas import router as fincas_router
from sectores import router as sectores_router
from trabajadores import router as trabajadores_router
from revisiones import router as revisiones_router
from usuarios import router as usuarios_router
from catalogos import router as catalogos_router  # 👈 NUEVO

from imagenes import router as imagenes_router

from auth_simple import require_api_key

# ------------------------
# APP (API_KEY GLOBAL)
# ------------------------
app = FastAPI(
    title="El Colibri API",
    dependencies=[Depends(require_api_key)]
)

# ------------------------
# CORS
# ------------------------
origins = [
    "http://localhost:5173",           # frontend local
    "https://elcolibriapp.vercel.app", # frontend producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     # usa ["*"] solo para pruebas locales
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# REGISTRAR ROUTERS
# ------------------------
app.include_router(fincas_router)
app.include_router(sectores_router)
app.include_router(trabajadores_router)
app.include_router(revisiones_router)
app.include_router(usuarios_router)
app.include_router(catalogos_router)  # 👈 CATÁLOGOS

app.include_router(imagenes_router)

# ------------------------
# RUTA RAÍZ
# ------------------------
@app.get("/")
def root():
    return {"status": "ok"}

