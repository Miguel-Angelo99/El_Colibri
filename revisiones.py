from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import RevisionCreate, RevisionResponse
from crud_revisiones import crear_revision, listar_revisiones, obtener_revision, eliminar_revision

router = APIRouter(prefix="/revisiones", tags=["Revisiones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=RevisionResponse)
def create_revision(body: RevisionCreate, db: Session = Depends(get_db)):
    rev, err = crear_revision(db, body)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return rev


@router.get("", response_model=list[RevisionResponse])
def get_revisiones(
    sector_id: int | None = Query(default=None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return listar_revisiones(db, sector_id=sector_id, skip=skip, limit=limit)


@router.get("/{revision_id}", response_model=RevisionResponse)
def get_revision(revision_id: int, db: Session = Depends(get_db)):
    rev = obtener_revision(db, revision_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Revisión no existe")
    return rev


@router.delete("/{revision_id}")
def delete_revision(revision_id: int, db: Session = Depends(get_db)):
    ok = eliminar_revision(db, revision_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Revisión no existe")
    return {"ok": True}
