from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from fincas import router as fincas_router
from sectores import router as sectores_router


from database import engine, SessionLocal
from models import Base
from schemas import UsuarioCreate, UsuarioResponse
#from crud import crear_usuario

from revisiones import router as revisiones_router

app = FastAPI()
app.include_router(revisiones_router)
app.include_router(fincas_router)
app.include_router(sectores_router)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/usuarios", response_model=UsuarioResponse)
def crear(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return crear_usuario(db, usuario)


@app.get("/")
def root():
    return {"status": "ok"}

