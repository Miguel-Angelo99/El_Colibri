# crud_sectores.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Sector, Finca
from schemas import SectorCreate, SectorUpdate


def crear_sector(db: Session, data: SectorCreate):
    # valida finca
    finca = db.query(Finca).filter(Finca.id == data.finca_id).first()
    if not finca:
        return None, "Finca no existe"

    if data.num_plantas <= 0:
        return None, "num_plantas debe ser > 0"

    sector = Sector(
        finca_id=data.finca_id,
        nombre=data.nombre.strip(),
        num_plantas=int(data.num_plantas),
        ubicacion=(data.ubicacion.strip() if data.ubicacion else None),
    )

    db.add(sector)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Ya existe un sector con ese nombre en esta finca"

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

    if data.num_plantas is not None:
        if data.num_plantas <= 0:
            return None, "num_plantas debe ser > 0"
        sector.num_plantas = int(data.num_plantas)

    if data.ubicacion is not None:
        sector.ubicacion = data.ubicacion.strip() if data.ubicacion else None

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Conflicto: nombre duplicado en la finca"

    db.refresh(sector)
    return sector, None


def eliminar_sector(db: Session, sector_id: int) -> bool:
    sector = obtener_sector(db, sector_id)
    if not sector:
        return False
    db.delete(sector)
    db.commit()
    return True
