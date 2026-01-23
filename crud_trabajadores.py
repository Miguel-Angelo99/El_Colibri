from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models import Trabajador
from schemas import TrabajadorCreate, TrabajadorUpdate


def crear_trabajador(db: Session, data: TrabajadorCreate):
    obj = Trabajador(
        nombre=data.nombre.strip(),
        apellido=data.apellido.strip(),
        dni=data.dni.strip() if data.dni else None,
        telefono=data.telefono.strip() if data.telefono else None,
        email=str(data.email).strip() if data.email else None,
        fecha_ingreso=data.fecha_ingreso,
        puesto=data.puesto.strip() if data.puesto else None,
        activo=True if data.activo is None else bool(data.activo),
    )

    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "DNI duplicado (ya existe un trabajador con ese DNI)"

    db.refresh(obj)
    return obj, None


def listar_trabajadores(db: Session, activo: bool | None = None, skip: int = 0, limit: int = 50):
    q = db.query(Trabajador)
    if activo is not None:
        q = q.filter(Trabajador.activo == activo)
    return q.order_by(Trabajador.id.asc()).offset(skip).limit(limit).all()


def obtener_trabajador(db: Session, trabajador_id: int):
    return db.query(Trabajador).filter(Trabajador.id == trabajador_id).first()


def actualizar_trabajador(db: Session, trabajador_id: int, data: TrabajadorUpdate):
    obj = obtener_trabajador(db, trabajador_id)
    if not obj:
        return None, "Trabajador no existe"

    if data.nombre is not None:
        obj.nombre = data.nombre.strip()
    if data.apellido is not None:
        obj.apellido = data.apellido.strip()
    if data.dni is not None:
        obj.dni = data.dni.strip() if data.dni else None
    if data.telefono is not None:
        obj.telefono = data.telefono.strip() if data.telefono else None
    if data.email is not None:
        obj.email = str(data.email).strip() if data.email else None
    if data.fecha_ingreso is not None:
        obj.fecha_ingreso = data.fecha_ingreso
    if data.puesto is not None:
        obj.puesto = data.puesto.strip() if data.puesto else None
    if data.activo is not None:
        obj.activo = bool(data.activo)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "DNI duplicado (ya existe otro trabajador con ese DNI)"

    db.refresh(obj)
    return obj, None


def eliminar_trabajador(db: Session, trabajador_id: int):
    obj = obtener_trabajador(db, trabajador_id)
    if not obj:
        return False

    db.delete(obj)
    db.commit()
    return True
