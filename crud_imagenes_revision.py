# crud_imagenes_revision.py
from sqlalchemy.orm import Session

# Ajusta el import si tu clase no se llama Imagen
from imagenes import Imagen  # si tu modelo está en imagenes.py


def _set_if_exists(obj, candidates: list[str], value):
    for attr in candidates:
        if hasattr(obj, attr):
            setattr(obj, attr, value)
            return True
    return False


def guardar_imagenes_revision(db: Session, revision_id: int, items: list[dict]) -> int:
    """
    items:
      [{original_name, stored_name, rel_path, order_index}]
    """
    # borrar lo previo (si re-suben zip)
    if hasattr(Imagen, "revision_id"):
        db.query(Imagen).filter(Imagen.revision_id == revision_id).delete()
    else:
        # si tu modelo no tiene revision_id, esto no puede funcionar correctamente
        raise RuntimeError("Tu modelo Imagen no tiene campo revision_id. Pásame imagenes.py y lo ajusto.")

    for it in items:
        img = Imagen()

        # FK
        setattr(img, "revision_id", revision_id)

        # original name
        _set_if_exists(img, ["nombre_original", "original_name", "archivo_original", "filename_original"], it["original_name"])

        # stored name
        _set_if_exists(img, ["nombre_archivo", "archivo", "filename", "stored_name", "key"], it["stored_name"])

        # relative path
        _set_if_exists(img, ["ruta", "path", "rel_path", "url", "storage_path"], it["rel_path"])

        # order
        _set_if_exists(img, ["orden", "order_index", "indice", "index"], it["order_index"])

        db.add(img)

    db.commit()
    return len(items)
