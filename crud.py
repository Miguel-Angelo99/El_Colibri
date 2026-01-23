from sqlalchemy.orm import Session
from models import Usuario
from schemas import UsuarioCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def crear_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
    nuevo = Usuario(
        email=usuario.email,
        password_hash=_hash_password(usuario.password),
        role=UserRole.user,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

