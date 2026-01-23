# revisiones.py
from datetime import date
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import (
    RevisionCreateResponse, RevisionImagenListResponse,
    RevisionValidarResponse, RevisionFinalizarRequest, RevisionFinalizarResponse
)
from crud_revisiones import (
    crear_revision_desde_zip, listar_imagenes_revision,
    borrar_imagen_revision, subir_imagenes_a_revision,
    validar_cantidad, finalizar_revision
)

router = APIRouter(prefix="/revisiones", tags=["Revisiones"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=RevisionCreateResponse)
async def crear_revision(
    finca_id: int = Form(...),
    sector_id: int = Form(...),
    fecha_revision: date = Form(...),
    tipo_revision: str = Form(None),
    zip_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not zip_file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .zip")

    zip_bytes = await zip_file.read()

    try:
        rev = crear_revision_desde_zip(
            db=db,
            finca_id=finca_id,
            sector_id=sector_id,
            fecha_revision=fecha_revision,
            tipo_revision=tipo_revision,
            zip_bytes=zip_bytes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # total en DB
    total = len(rev.imagenes)
    return {
        "revision_id": rev.id,
        "total": total,
        "esperadas": rev.num_plantas_esperadas,
        "estado": rev.estado,
    }


@router.get("/{revision_id}/imagenes", response_model=RevisionImagenListResponse)
def get_imagenes(revision_id: int, db: Session = Depends(get_db)):
    try:
        rev, imgs = listar_imagenes_revision(db, revision_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "revision_id": rev.id,
        "total": len(imgs),
        "esperadas": rev.num_plantas_esperadas,
        "estado": rev.estado,
        "imagenes": imgs,
    }


@router.delete("/{revision_id}/imagenes/{image_id}")
def delete_imagen(revision_id: int, image_id: int, db: Session = Depends(get_db)):
    try:
        borrar_imagen_revision(db, revision_id, image_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {"ok": True}


@router.post("/{revision_id}/imagenes")
async def upload_imagenes(
    revision_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    payload = []
    for f in files:
        content = await f.read()
        payload.append((f.filename, content))

    try:
        subir_imagenes_a_revision(db, revision_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"ok": True}


@router.post("/{revision_id}/validar", response_model=RevisionValidarResponse)
def validar_revision(revision_id: int, db: Session = Depends(get_db)):
    try:
        total, esperadas, ok = validar_cantidad(db, revision_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "revision_id": revision_id,
        "total": total,
        "esperadas": esperadas,
        "ok": ok,
    }


@router.post("/{revision_id}/finalizar", response_model=RevisionFinalizarResponse)
def finalizar(
    revision_id: int,
    body: RevisionFinalizarRequest,
    db: Session = Depends(get_db),
):
    asignaciones = [{"image_id": a.image_id, "numero": a.numero} for a in body.asignaciones]

    try:
        rev, numeros = finalizar_revision(db, revision_id, asignaciones)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # total final
    total = len(rev.imagenes)
    return {
        "revision_id": rev.id,
        "estado": rev.estado,
        "total": total,
        "esperadas": rev.num_plantas_esperadas,
        "numeros": numeros,
    }
