from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from fincas import router as fincas_router
from sectores import router as sectores_router
from trabajadores import router as trabajadores_router
from revisiones import router as revisiones_router
from usuarios import router as usuarios_router
from catalogos import router as catalogos_router
from imagenes import router as imagenes_router

from auth_simple import require_api_key

# ------------------------
# Crear carpeta storage para StaticFiles
# ------------------------
Path("storage").mkdir(parents=True, exist_ok=True)

# ------------------------
# APP (API_KEY GLOBAL)
# ------------------------
app = FastAPI(
    title="El Colibri API",
    dependencies=[Depends(require_api_key)]
)

# ------------------------
# Montar estáticos DESPUÉS de crear app
# ------------------------
app.mount("/static", StaticFiles(directory="storage"), name="static")

# ------------------------
# CORS
# ------------------------
origins = [
    "http://localhost:5173",
    "https://elcolibriapp.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],    # Permite GET, POST, PUT, DELETE, OPTIONS, etc.
    allow_headers=["*"],    # Permite todos los headers (incluyendo x-api-key)
)

# ------------------------
# REGISTRAR ROUTERS
# ------------------------
app.include_router(fincas_router)
app.include_router(sectores_router)
app.include_router(trabajadores_router)
app.include_router(revisiones_router)
app.include_router(usuarios_router)
app.include_router(catalogos_router)
app.include_router(imagenes_router)

# ------------------------
# RUTA RAÍZ
# ------------------------
@app.get("/")
def root():
    return {"status": "ok"}
