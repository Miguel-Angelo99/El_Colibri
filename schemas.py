from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# =========================
# FINCA
# =========================
class FincaBase(BaseModel):
    nombre: str
    ubicacion: Optional[str] = None
    tamano_hectareas: Optional[Decimal] = None


class FincaCreate(FincaBase):
    pass


class FincaUpdate(BaseModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    tamano_hectareas: Optional[Decimal] = None


class FincaResponse(FincaBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================
# SECTOR
# =========================
class SectorBase(BaseModel):
    finca_id: int
    nombre: str
    descripcion: Optional[str] = None
    area_hectareas: Optional[Decimal] = None
    plantas_cantidad: Optional[Decimal] = None


class SectorCreate(SectorBase):
    pass


class SectorUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    area_hectareas: Optional[Decimal] = None
    plantas_cantidad: Optional[Decimal] = None


class SectorResponse(SectorBase):
    id: int

    class Config:
        from_attributes = True


# =========================
# USUARIO
# =========================
class UsuarioBase(BaseModel):
    email: EmailStr


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)


class UsuarioResponse(UsuarioBase):
    id: int
    is_active: bool
    email_verified: bool
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =========================
# REVISION (BÁSICO)
# =========================
class RevisionCreate(BaseModel):
    sector_id: int
    fecha_revision: date
    tipo: str  # debe ser un valor EXACTO del enum tipo_revision (ej "Revision mensual")
    observaciones: Optional[str] = None
    comentario: Optional[str] = None
    usuario_id: Optional[int] = None


class RevisionResponse(RevisionCreate):
    id: int

    class Config:
        from_attributes = True



class TrabajadorBase(BaseModel):
    nombre: str
    apellido: str
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    fecha_ingreso: Optional[date] = None
    puesto: Optional[str] = None
    activo: Optional[bool] = True


class TrabajadorCreate(TrabajadorBase):
    pass


class TrabajadorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None
    fecha_ingreso: Optional[date] = None
    puesto: Optional[str] = None
    activo: Optional[bool] = None


class TrabajadorResponse(TrabajadorBase):
    id: int
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True

