from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from models import Usuario
from schemas import UsuarioCreate, UsuarioUpdate, UsuarioPasswordUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def crear_usuario(db: Session, data: UsuarioCreate) -> tuple[Optional[Usuario], Optional[str]]:
    email = data.email.strip().lower()

    nuevo = Usuario(
        email=email,
        password_hash=_hash_password(data.password),
        role=(data.role.strip() if data.role else "user"),
        is_active=True,
        email_verified=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(nuevo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Ya existe un usuario con ese email"
    db.refresh(nuevo)
    return nuevo, None


def listar_usuarios(db: Session, skip: int = 0, limit: int = 50):
    return (
        db.query(Usuario)
        .order_by(Usuario.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def obtener_usuario(db: Session, usuario_id: int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def obtener_usuario_por_email(db: Session, email: str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email == email.strip().lower()).first()


def actualizar_usuario(db: Session, usuario_id: int, data: UsuarioUpdate) -> tuple[Optional[Usuario], Optional[str]]:
    u = obtener_usuario(db, usuario_id)
    if not u:
        return None, "Usuario no existe"

    if data.email is not None:
        u.email = data.email.strip().lower()

    if data.is_active is not None:
        u.is_active = bool(data.is_active)

    if data.email_verified is not None:
        u.email_verified = bool(data.email_verified)

    if data.role is not None:
        u.role = data.role.strip()

    u.updated_at = datetime.utcnow()

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None, "Conflicto: email duplicado"
    db.refresh(u)
    return u, None


def actualizar_password(db: Session, usuario_id: int, data: UsuarioPasswordUpdate) -> tuple[bool, Optional[str]]:
    u = obtener_usuario(db, usuario_id)
    if not u:
        return False, "Usuario no existe"

    u.password_hash = _hash_password(data.new_password)
    u.password_changed_at = datetime.utcnow()
    u.updated_at = datetime.utcnow()

    db.commit()
    return True, None


def eliminar_usuario(db: Session, usuario_id: int) -> bool:
    u = obtener_usuario(db, usuario_id)
    if not u:
        return False
    db.delete(u)
    db.commit()
    return True
