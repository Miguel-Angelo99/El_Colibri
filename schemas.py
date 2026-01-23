from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


class UsuarioBase(BaseModel):
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioResponse(UsuarioBase):
    id: int
    is_active: bool
    email_verified: bool
    role: str
    permissions: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Revisiones =====

class RevisionCreateResponse(BaseModel):
    revision_id: int
    total: int
    esperadas: int
    estado: str


class RevisionImagenOut(BaseModel):
    id: int
    idx: int
    numero_etiqueta: Optional[str] = None
    estado: str
    storage_key: str

    class Config:
        from_attributes = True


class RevisionImagenListResponse(BaseModel):
    revision_id: int
    total: int
    esperadas: int
    estado: str
    imagenes: List[RevisionImagenOut]


class RevisionValidarResponse(BaseModel):
    revision_id: int
    total: int
    esperadas: int
    ok: bool


class AsignacionNumero(BaseModel):
    image_id: int
    numero: str = Field(..., min_length=1, max_length=5, pattern=r"^\d{1,5}$")


class RevisionFinalizarRequest(BaseModel):
    asignaciones: List[AsignacionNumero]


class RevisionFinalizarResponse(BaseModel):
    revision_id: int
    estado: str
    total: int
    esperadas: int
    numeros: List[str]

# ===== FINCAS =====

from typing import Optional, List

class FincaBase(BaseModel):
    nombre: str
    ubicacion: Optional[str] = None
    estado: Optional[str] = None
    owner: Optional[str] = None


class FincaCreate(FincaBase):
    pass


class FincaUpdate(BaseModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    estado: Optional[str] = None
    owner: Optional[str] = None


class FincaResponse(FincaBase):
    id: int
    class Config:
        from_attributes = True


# ===== SECTORES =====

class SectorBase(BaseModel):
    finca_id: int
    nombre: str
    num_plantas: int
    ubicacion: Optional[str] = None


class SectorCreate(SectorBase):
    pass


class SectorUpdate(BaseModel):
    nombre: Optional[str] = None
    num_plantas: Optional[int] = None
    ubicacion: Optional[str] = None


class SectorResponse(SectorBase):
    id: int
    class Config:
        from_attributes = True
