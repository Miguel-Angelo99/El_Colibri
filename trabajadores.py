from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import TrabajadorCreate, TrabajadorUpdate, TrabajadorResponse
from crud_trabajadores import (
    crear_trabajador, listar_trabajadores, obtener_trabajador,
    actualizar_trabajador, eliminar_trabajador
)

router = APIRouter(prefix="/trabajadores", tags=["Trabajadores"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=TrabajadorResponse)
def create_trabajador(body: TrabajadorCreate, db: Session = Depends(get_db)):
    obj, err = crear_trabajador(db, body)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return obj


@router.get("", response_model=list[TrabajadorResponse])
def get_trabajadores(
    activo: bool | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return listar_trabajadores(db, activo=activo, skip=skip, limit=limit)


@router.get("/{trabajador_id}", response_model=TrabajadorResponse)
def get_trabajador(trabajador_id: int, db: Session = Depends(get_db)):
    obj = obtener_trabajador(db, trabajador_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Trabajador no existe")
    return obj


@router.put("/{trabajador_id}", response_model=TrabajadorResponse)
def put_trabajador(trabajador_id: int, body: TrabajadorUpdate, db: Session = Depends(get_db)):
    obj, err = actualizar_trabajador(db, trabajador_id, body)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return obj


@router.delete("/{trabajador_id}")
def delete_trabajador(trabajador_id: int, db: Session = Depends(get_db)):
    ok = eliminar_trabajador(db, trabajador_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Trabajador no existe")
    return {"ok": True}
