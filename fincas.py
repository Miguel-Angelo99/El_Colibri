# fincas.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import FincaCreate, FincaUpdate, FincaResponse
from crud_fincas import crear_finca, listar_fincas, obtener_finca, actualizar_finca, eliminar_finca

router = APIRouter(prefix="/fincas", tags=["Fincas"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=FincaResponse)
def create_finca(body: FincaCreate, db: Session = Depends(get_db)):
    return crear_finca(db, body)


@router.get("", response_model=list[FincaResponse])
def get_fincas(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return listar_fincas(db, skip=skip, limit=limit)


@router.get("/{finca_id}", response_model=FincaResponse)
def get_finca(finca_id: int, db: Session = Depends(get_db)):
    finca = obtener_finca(db, finca_id)
    if not finca:
        raise HTTPException(status_code=404, detail="Finca no existe")
    return finca


@router.put("/{finca_id}", response_model=FincaResponse)
def put_finca(finca_id: int, body: FincaUpdate, db: Session = Depends(get_db)):
    finca = actualizar_finca(db, finca_id, body)
    if not finca:
        raise HTTPException(status_code=404, detail="Finca no existe")
    return finca


@router.delete("/{finca_id}")
def delete_finca(finca_id: int, db: Session = Depends(get_db)):
    ok = eliminar_finca(db, finca_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Finca no existe")
    return {"ok": True}
