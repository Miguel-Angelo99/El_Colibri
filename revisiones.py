from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import RevisionCreate, RevisionResponse
from crud_revisiones import crear_revision, listar_revisiones, obtener_revision, eliminar_revision

from fastapi import UploadFile, File
from services.zip_processor import procesar_zip_revision_local
from crud_imagenes import guardar_imagenes_revision
from crud_revisiones import obtener_revision



from crud_imagenes import guardar_imagenes_revision  # te lo dejo abajo


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



@router.post("/{revision_id}/zip", response_model=dict)
def upload_zip_revision(
    revision_id: int,
    zipfile: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    rev = obtener_revision(db, revision_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Revisión no existe")

    # ✅ Si quieres validar cantidad contra plantas del sector:
    # - opción 1 (si tu revisión tiene plantas_esperadas): expected = getattr(rev, "plantas_esperadas", None)
    # - opción 2 (si quieres contar plantas por sector): usa crud_plantas.count_plants_by_sector(...)
    expected = getattr(rev, "plantas_esperadas", None)

    items = procesar_zip_revision_local(
        revision_id=revision_id,
        zip_file=zipfile,
        storage_root="storage",
        expected_count=expected,
    )

    count = guardar_imagenes_revision(db, revision_id, items)

    return {
        "revision_id": revision_id,
        "count": count,
        "items": items,
        "static_base": "/static",  # para que el front arme /static/<rel_path>
    }


@router.post("/{revision_id}/zip", response_model=dict)
def upload_zip_revision(
    revision_id: int,
    zipfile: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    rev = obtener_revision(db, revision_id)
    if not rev:
        raise HTTPException(status_code=404, detail="Revisión no existe")

    # ✅ si tienes un campo plantas_esperadas en revisiones:
    expected = getattr(rev, "plantas_esperadas", None)

    items = procesar_zip_revision_local(
        revision_id=revision_id,
        zip_file=zipfile,
        storage_root="storage",
        expected_count=expected,
    )

    # guardar registro de cada foto en DB
    count = guardar_imagenes_revision(db, revision_id, items)

    return {
        "revision_id": revision_id,
        "count": count,
        "items": items,
        "static_base": "/static",
    }





