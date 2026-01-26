from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Revision, Sector, TipoRevision
from schemas import RevisionCreate


def crear_revision(db: Session, data: RevisionCreate):
    sector = db.query(Sector).filter(Sector.id == data.sector_id).first()
    if not sector:
        return None, "Sector no existe"

    # Validar que el tipo sea uno de los valores del ENUM
    valid_values = {e.value for e in TipoRevision}
    if data.tipo not in valid_values:
        return None, f"tipo inválido. Debe ser uno de: {sorted(list(valid_values))}"

    rev = Revision(
        sector_id=data.sector_id,
        fecha_revision=data.fecha_revision,
        tipo=data.tipo,  # SQLAlchemy Enum acepta el string value
        observaciones=data.observaciones,
        comentario=data.comentario,
        usuario_id=data.usuario_id,
    )

    db.add(rev)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Error creando revisión"

    db.refresh(rev)
    return rev, None


def listar_revisiones(db: Session, sector_id: int | None = None, skip: int = 0, limit: int = 50):
    q = db.query(Revision)
    if sector_id is not None:
        q = q.filter(Revision.sector_id == sector_id)
    return q.order_by(Revision.id.desc()).offset(skip).limit(limit).all()


def obtener_revision(db: Session, revision_id: int):
    return db.query(Revision).filter(Revision.id == revision_id).first()


def eliminar_revision(db: Session, revision_id: int) -> bool:
    rev = obtener_revision(db, revision_id)
    if not rev:
        return False
    db.delete(rev)
    db.commit()
    return True


