# crud_fincas.py
from sqlalchemy.orm import Session
from models import Finca
from schemas import FincaCreate, FincaUpdate


def crear_finca(db: Session, data: FincaCreate) -> Finca:
    finca = Finca(
        nombre=data.nombre.strip(),
        ubicacion=(data.ubicacion.strip() if data.ubicacion else None),
        estado=(data.estado.strip() if data.estado else None),
        owner=(data.owner.strip() if data.owner else None),
    )
    db.add(finca)
    db.commit()
    db.refresh(finca)
    return finca


def listar_fincas(db: Session, skip: int = 0, limit: int = 50):
    return db.query(Finca).order_by(Finca.id.asc()).offset(skip).limit(limit).all()


def obtener_finca(db: Session, finca_id: int):
    return db.query(Finca).filter(Finca.id == finca_id).first()


def actualizar_finca(db: Session, finca_id: int, data: FincaUpdate):
    finca = obtener_finca(db, finca_id)
    if not finca:
        return None

    if data.nombre is not None:
        finca.nombre = data.nombre.strip()
    if data.ubicacion is not None:
        finca.ubicacion = data.ubicacion.strip() if data.ubicacion else None
    if data.estado is not None:
        finca.estado = data.estado.strip() if data.estado else None
    if data.owner is not None:
        finca.owner = data.owner.strip() if data.owner else None

    db.commit()
    db.refresh(finca)
    return finca


def eliminar_finca(db: Session, finca_id: int) -> bool:
    finca = obtener_finca(db, finca_id)
    if not finca:
        return False
    db.delete(finca)
    db.commit()
    return True
