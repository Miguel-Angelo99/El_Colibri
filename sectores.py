from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import SectorCreate, SectorUpdate, SectorResponse
from crud_sectores import crear_sector, listar_sectores, obtener_sector, actualizar_sector, eliminar_sector

router = APIRouter(prefix="/sectores", tags=["Sectores"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=SectorResponse)
def create_sector(body: SectorCreate, db: Session = Depends(get_db)):
    sector, err = crear_sector(db, body)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return sector


@router.get("", response_model=list[SectorResponse])
def get_sectores(
    finca_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return listar_sectores(db, finca_id=finca_id, skip=skip, limit=limit)


@router.get("/{sector_id}", response_model=SectorResponse)
def get_sector(sector_id: int, db: Session = Depends(get_db)):
    sector = obtener_sector(db, sector_id)
    if not sector:
        raise HTTPException(status_code=404, detail="Sector no existe")
    return sector


@router.put("/{sector_id}", response_model=SectorResponse)
def put_sector(sector_id: int, body: SectorUpdate, db: Session = Depends(get_db)):
    sector, err = actualizar_sector(db, sector_id, body)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return sector


@router.delete("/{sector_id}")
def delete_sector(sector_id: int, db: Session = Depends(get_db)):
    ok = eliminar_sector(db, sector_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sector no existe")
    return {"ok": True}
