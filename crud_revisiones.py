# crud_revisiones.py
import os
import io
import shutil
import zipfile
from pathlib import Path
from datetime import date
from typing import List, Dict, Optional, Tuple

from PIL import Image

from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Finca, Sector, Revision, RevisionImagen


ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
DATA_DIR = Path("data")


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _is_image_name(name: str) -> bool:
    ext = Path(name).suffix.lower()
    return ext in ALLOWED_EXTS


def _save_as_jpg(src_bytes: bytes, dst_path: Path) -> None:
    """Convierte a JPG para un formato uniforme (mejor para el front y renombres)."""
    img = Image.open(io.BytesIO(src_bytes))  # noqa: F821
    img = img.convert("RGB")
    img.save(dst_path, format="JPEG", quality=92)


def _safe_filename(name: str) -> str:
    # evita paths dentro del zip tipo ../../
    return Path(name).name


def _staging_dir(finca_id: int, sector_id: int, revision_id: int) -> Path:
    return DATA_DIR / f"finca_{finca_id}" / f"sector_{sector_id}" / f"revision_{revision_id}" / "staging"


def _final_dir(finca_id: int, sector_id: int, revision_id: int) -> Path:
    return DATA_DIR / f"finca_{finca_id}" / f"sector_{sector_id}" / f"revision_{revision_id}" / "final"


def _planta_dir(finca_id: int, sector_id: int, revision_id: int, numero: str) -> Path:
    return _final_dir(finca_id, sector_id, revision_id) / f"planta_{numero}"


def _reindex_staging(db: Session, revision_id: int) -> None:
    """Re-indexa idx 1..X según orden actual en DB (por id) y renombra físicamente."""
    imgs: List[RevisionImagen] = (
        db.query(RevisionImagen)
        .filter(RevisionImagen.revision_id == revision_id)
        .order_by(RevisionImagen.id.asc())
        .all()
    )

    for new_idx, img in enumerate(imgs, start=1):
        if img.idx == new_idx:
            continue

        old_path = Path(img.storage_key)
        new_path = old_path.with_name(f"{new_idx}.jpg")

        if old_path.exists():
            old_path.rename(new_path)

        img.idx = new_idx
        img.storage_key = str(new_path)

    db.commit()


def crear_revision_desde_zip(
    db: Session,
    finca_id: int,
    sector_id: int,
    fecha_revision: date,
    tipo_revision: Optional[str],
    zip_bytes: bytes,
) -> Revision:
    # Validaciones de catálogo
    finca = db.query(Finca).filter(Finca.id == finca_id).first()
    if not finca:
        raise ValueError("Finca no existe")

    sector = db.query(Sector).filter(Sector.id == sector_id).first()
    if not sector:
        raise ValueError("Sector no existe")

    if sector.finca_id != finca_id:
        raise ValueError("El sector no pertenece a la finca indicada")

    # Leer ZIP en memoria
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))  # noqa: F821
    except zipfile.BadZipFile:
        raise ValueError("ZIP inválido o corrupto")

    image_names = [n for n in zf.namelist() if _is_image_name(n)]
    total = len(image_names)
    esperadas = int(sector.num_plantas)

    # Regla del negocio: al crear, deben coincidir
    if total != esperadas:
        raise ValueError(f"La cantidad de fotos no es válida: total={total}, esperadas={esperadas}")

    # Crear Revision en DB
    rev = Revision(
        finca_id=finca_id,
        sector_id=sector_id,
        fecha_revision=fecha_revision,
        tipo_revision=tipo_revision,
        num_plantas_esperadas=esperadas,
        estado="STAGING",
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)

    st_dir = _staging_dir(finca_id, sector_id, rev.id)
    _ensure_dir(st_dir)

    # Guardar imágenes renombradas 1..X.jpg
    # Orden estable: nombre del zip ordenado
    image_names.sort()

    for idx, name in enumerate(image_names, start=1):
        safe = _safe_filename(name)
        raw = zf.read(name)

        # Guardamos todo como JPG (uniforme)
        out_path = st_dir / f"{idx}.jpg"
        img = Image.open(io.BytesIO(raw))  # noqa: F821
        img = img.convert("RGB")
        img.save(out_path, format="JPEG", quality=92)

        db_img = RevisionImagen(
            revision_id=rev.id,
            idx=idx,
            estado="STAGING",
            numero_etiqueta=None,
            storage_key=str(out_path),
            filename_original=safe,
        )
        db.add(db_img)

    db.commit()
    return rev


def listar_imagenes_revision(db: Session, revision_id: int) -> Tuple[Revision, List[RevisionImagen]]:
    rev = db.query(Revision).filter(Revision.id == revision_id).first()
    if not rev:
        raise ValueError("Revisión no existe")

    imgs = (
        db.query(RevisionImagen)
        .filter(RevisionImagen.revision_id == revision_id)
        .order_by(RevisionImagen.idx.asc())
        .all()
    )
    return rev, imgs


def borrar_imagen_revision(db: Session, revision_id: int, image_id: int) -> None:
    img = (
        db.query(RevisionImagen)
        .filter(and_(RevisionImagen.revision_id == revision_id, RevisionImagen.id == image_id))
        .first()
    )
    if not img:
        raise ValueError("Imagen no existe en esta revisión")

    # borrar archivo
    p = Path(img.storage_key)
    if p.exists():
        p.unlink(missing_ok=True)

    db.delete(img)
    db.commit()

    # reindex para mantener 1..X
    _reindex_staging(db, revision_id)


def subir_imagenes_a_revision(db: Session, revision_id: int, files: List[Tuple[str, bytes]]) -> None:
    rev = db.query(Revision).filter(Revision.id == revision_id).first()
    if not rev:
        raise ValueError("Revisión no existe")

    if rev.estado != "STAGING":
        raise ValueError("Solo se puede subir imágenes en estado STAGING")

    finca_id = rev.finca_id
    sector_id = rev.sector_id

    st_dir = _staging_dir(finca_id, sector_id, rev.id)
    _ensure_dir(st_dir)

    # idx siguiente
    current = db.query(RevisionImagen).filter(RevisionImagen.revision_id == revision_id).count()
    next_idx = current + 1

    for filename, content in files:
        # convertir a jpg
        out_path = st_dir / f"{next_idx}.jpg"
        img = Image.open(io.BytesIO(content))  # noqa: F821
        img = img.convert("RGB")
        img.save(out_path, format="JPEG", quality=92)

        db_img = RevisionImagen(
            revision_id=revision_id,
            idx=next_idx,
            estado="STAGING",
            numero_etiqueta=None,
            storage_key=str(out_path),
            filename_original=Path(filename).name,
        )
        db.add(db_img)
        next_idx += 1

    db.commit()


def validar_cantidad(db: Session, revision_id: int) -> Tuple[int, int, bool]:
    rev = db.query(Revision).filter(Revision.id == revision_id).first()
    if not rev:
        raise ValueError("Revisión no existe")

    total = db.query(RevisionImagen).filter(RevisionImagen.revision_id == revision_id).count()
    esperadas = rev.num_plantas_esperadas
    return total, esperadas, (total == esperadas)


def finalizar_revision(
    db: Session,
    revision_id: int,
    asignaciones: List[Dict[str, str]],
) -> Tuple[Revision, List[str]]:
    rev = db.query(Revision).filter(Revision.id == revision_id).first()
    if not rev:
        raise ValueError("Revisión no existe")

    if rev.estado != "STAGING":
        raise ValueError("La revisión no está en STAGING")

    # validar cantidad actual
    total, esperadas, ok = validar_cantidad(db, revision_id)
    if not ok:
        raise ValueError(f"No coincide la cantidad: total={total}, esperadas={esperadas}")

    # asignaciones -> map
    if len(asignaciones) != total:
        raise ValueError("Debe asignar un número a cada imagen")

    # validar dígitos y duplicados dentro de la revisión
    numeros = []
    seen = set()
    mapping: Dict[int, str] = {}

    for a in asignaciones:
        image_id = int(a["image_id"])
        numero = str(a["numero"]).strip()
        if not numero.isdigit() or not (1 <= len(numero) <= 5):
            raise ValueError("Número inválido (solo 1 a 5 dígitos)")

        if numero in seen:
            raise ValueError(f"Número repetido en la revisión: {numero}")

        seen.add(numero)
        numeros.append(numero)
        mapping[image_id] = numero

    # traer imágenes de la revisión
    imgs: List[RevisionImagen] = (
        db.query(RevisionImagen)
        .filter(RevisionImagen.revision_id == revision_id)
        .order_by(RevisionImagen.idx.asc())
        .all()
    )

    # validar que todos los ids enviados existan
    ids_db = {i.id for i in imgs}
    ids_req = set(mapping.keys())
    if ids_db != ids_req:
        raise ValueError("Asignaciones no coinciden con las imágenes actuales (faltan o sobran IDs)")

    finca_id = rev.finca_id
    sector_id = rev.sector_id

    # mover a final: finca/sector/revision/planta_NUM/idx_NUM.jpg
    for img in imgs:
        numero = mapping[img.id]

        dst_dir = _planta_dir(finca_id, sector_id, rev.id, numero)
        _ensure_dir(dst_dir)

        src = Path(img.storage_key)
        dst = dst_dir / f"{img.idx}_{numero}.jpg"

        if src.exists():
            shutil.move(str(src), str(dst))
        else:
            raise ValueError(f"Archivo no encontrado en staging: {src}")

        img.numero_etiqueta = numero
        img.estado = "FINAL"
        img.storage_key = str(dst)

    rev.estado = "FINALIZADA"
    db.commit()
    db.refresh(rev)

    return rev, numeros
