from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Sector, Finca
from schemas import SectorCreate, SectorUpdate


def crear_sector(db: Session, data: SectorCreate):
    finca = db.query(Finca).filter(Finca.id == data.finca_id).first()
    if not finca:
        return None, "Finca no existe"

    sector = Sector(
        finca_id=data.finca_id,
        nombre=data.nombre.strip(),
        descripcion=(data.descripcion.strip() if data.descripcion else None),
        area_hectareas=data.area_hectareas,
        plantas_cantidad=data.plantas_cantidad,
    )

    db.add(sector)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Conflicto al crear sector"

    db.refresh(sector)
    return sector, None


def listar_sectores(db: Session, finca_id: int | None = None, skip: int = 0, limit: int = 50):
    q = db.query(Sector)
    if finca_id is not None:
        q = q.filter(Sector.finca_id == finca_id)
    return q.order_by(Sector.id.asc()).offset(skip).limit(limit).all()


def obtener_sector(db: Session, sector_id: int):
    return db.query(Sector).filter(Sector.id == sector_id).first()


def actualizar_sector(db: Session, sector_id: int, data: SectorUpdate):
    sector = obtener_sector(db, sector_id)
    if not sector:
        return None, "Sector no existe"

    if data.nombre is not None:
        sector.nombre = data.nombre.strip()
    if data.descripcion is not None:
        sector.descripcion = data.descripcion.strip() if data.descripcion else None
    if data.area_hectareas is not None:
        sector.area_hectareas = data.area_hectareas
    if data.plantas_cantidad is not None:
        sector.plantas_cantidad = data.plantas_cantidad

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Conflicto al actualizar sector"

    db.refresh(sector)
    return sector, None


def eliminar_sector(db: Session, sector_id: int) -> bool:
    sector = obtener_sector(db, sector_id)
    if not sector:
        return False
    db.delete(sector)
    db.commit()
    return True
