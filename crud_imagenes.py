# crud_imagenes.py  (agrega esto al final)
from sqlalchemy.orm import Session
from imagenes import Imagen  # o from models import Imagen (según tu proyecto)

def borrar_imagenes_por_revision(db: Session, revision_id: int) -> None:
    db.query(Imagen).filter(Imagen.revision_id == revision_id).delete()
    db.commit()

def guardar_imagenes_revision(db: Session, revision_id: int, items: list[dict]) -> int:
    """
    items: [{original_name, stored_name, rel_path, order_index}]
    """
    # Reemplazar si ya existían
    db.query(Imagen).filter(Imagen.revision_id == revision_id).delete()

    for it in items:
        img = Imagen(
            revision_id=revision_id,
            nombre_original=it["original_name"],
            nombre_archivo=it["stored_name"],
            ruta=it["rel_path"],
            orden=it["order_index"],
        )
        db.add(img)

    db.commit()
    return len(items)
