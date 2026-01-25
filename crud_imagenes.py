# crud_imagenes.py
from sqlalchemy.orm import Session
from models import RevisionImagen

def borrar_imagenes_por_revision(db: Session, revision_id: int) -> None:
    db.query(RevisionImagen).filter(RevisionImagen.revision_id == revision_id).delete()
    db.commit()

def guardar_imagenes_revision(db: Session, revision_id: int, items: list[dict]) -> int:
    db.query(RevisionImagen).filter(RevisionImagen.revision_id == revision_id).delete()

    for it in items:
        db.add(RevisionImagen(
            revision_id=revision_id,
            nombre_original=it["original_name"],
            nombre_archivo=it["stored_name"],
            ruta=it["rel_path"],
            orden=it["order_index"],
        ))

    db.commit()
    return len(items)


