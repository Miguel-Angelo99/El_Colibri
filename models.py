import enum
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    Date,
    DateTime,
    Text,
    Numeric,
    ForeignKey,
    Enum as SAEnum,
    Table,
    func,
)
from sqlalchemy.orm import relationship
from database import Base


# =========================
# ENUMS (igual que en Postgres)
# =========================

class EstadoArbol(enum.Enum):
    bueno = "bueno"
    regular = "regular"
    malo = "malo"
    muerto = "muerto"


class EstadoPlanta(enum.Enum):
    viva = "viva"
    enferma = "enferma"
    muerta = "muerta"
    podada = "podada"
    en_observacion = "en observacion"  # ojo: en la BD es con espacio


class TipoImagen(enum.Enum):
    foto_general = "foto_general"
    foto_detalle = "foto_detalle"
    foto_danio = "foto_danio"
    otro = "otro"


class TipoRevision(enum.Enum):
    revision_mensual = "Revision mensual"
    revision_puesta_abono = "Revision por puesta de abono"
    revision_poda = "Revision por poda"
    revision_plagas_enfermedades = "Revision por plagas/enfermedades"
    revision_riego = "Revision de riego"
    revision_fertilizacion_foliar = "Revision de fertilizacion foliar"
    revision_soporte_tutorado = "Revision de soporte/tutorado"
    revision_cosecha = "Revision de cosecha"


# ==========================================================
# TABLA PIVOTE (revision_trabajador) (igual que en tu dump)
# ==========================================================

revision_trabajador = Table(
    "revision_trabajador",
    Base.metadata,
    Column(
        "revision_id",
        Integer,
        ForeignKey("revision.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "trabajador_id",
        Integer,
        ForeignKey("trabajador.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


# =========================
# TABLAS
# =========================

class Finca(Base):
    __tablename__ = "finca"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    ubicacion = Column(Text, nullable=True)
    tamano_hectareas = Column(Numeric(10, 2), nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=True)

    sectores = relationship(
        "Sector",
        back_populates="finca",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Sector(Base):
    __tablename__ = "sector"

    id = Column(Integer, primary_key=True, index=True)
    finca_id = Column(Integer, ForeignKey("finca.id", ondelete="CASCADE"), nullable=False)

    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    area_hectareas = Column(Numeric(10, 2), nullable=True)
    plantas_cantidad = Column(Numeric(10, 2), nullable=True)

    finca = relationship("Finca", back_populates="sectores")

    plantas = relationship(
        "Planta",
        back_populates="sector",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    revisiones = relationship(
        "Revision",
        back_populates="sector",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Planta(Base):
    __tablename__ = "planta"

    id = Column(BigInteger, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sector.id", ondelete="CASCADE"), nullable=False)

    numero = Column(Integer, nullable=False)
    especie = Column(String(100), nullable=True, server_default="Palta")
    procedencia = Column(String(150), nullable=True)
    fecha_nacimiento = Column(Date, nullable=True)

    estado = Column(
        SAEnum(EstadoPlanta, name="estado_planta", native_enum=True),
        nullable=False,
        server_default=EstadoPlanta.viva.value,
    )

    observaciones = Column(Text, nullable=True)
    fecha_plantacion = Column(Date, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=True)

    patron = Column(String(100), nullable=True)
    yema = Column(String(100), nullable=True)
    certificado_patron = Column(Boolean, nullable=True, server_default="false")
    certificado_yema = Column(Boolean, nullable=True, server_default="false")

    sector = relationship("Sector", back_populates="plantas")

    revisiones_unitarias = relationship(
        "RevisionUnitaria",
        back_populates="planta",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, nullable=True, server_default="true")
    email_verified = Column(Boolean, nullable=True, server_default="false")

    failed_attempts = Column(Integer, nullable=True, server_default="0")
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)

    remember_token = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    role = Column(String(50), nullable=True, server_default="user")
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), nullable=True)
    last_login = Column(DateTime, nullable=True)

    revisiones = relationship(
        "Revision",
        back_populates="usuario",
        passive_deletes=True,
    )


class Revision(Base):
    __tablename__ = "revision"

    id = Column(Integer, primary_key=True, index=True)
    sector_id = Column(Integer, ForeignKey("sector.id", ondelete="CASCADE"), nullable=False)

    fecha_revision = Column(Date, nullable=False)

    tipo = Column(
        SAEnum(TipoRevision, name="tipo_revision", native_enum=True),
        nullable=False,
    )

    observaciones = Column(Text, nullable=True)
    comentario = Column(Text, nullable=True)

    usuario_id = Column(BigInteger, ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True)

    sector = relationship("Sector", back_populates="revisiones")
    usuario = relationship("Usuario", back_populates="revisiones")

    trabajadores = relationship(
        "Trabajador",
        secondary=revision_trabajador,
        back_populates="revisiones",
    )

    unidades = relationship(
        "RevisionUnitaria",
        back_populates="revision",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class RevisionUnitaria(Base):
    __tablename__ = "revision_unitaria"

    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("revision.id", ondelete="CASCADE"), nullable=False)

    arbol_numero = Column(Integer, nullable=False)

    estado = Column(
        SAEnum(EstadoArbol, name="estado_arbol", native_enum=True),
        nullable=False,
    )

    observaciones = Column(Text, nullable=True)
    planta_id = Column(BigInteger, ForeignKey("planta.id", ondelete="CASCADE"), nullable=True)
    calificacion = Column(Numeric(3, 2), nullable=True)

    revision = relationship("Revision", back_populates="unidades")
    planta = relationship("Planta", back_populates="revisiones_unitarias")

    imagenes = relationship(
        "Imagen",
        back_populates="revision_unitaria",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Imagen(Base):
    __tablename__ = "imagen"

    id = Column(BigInteger, primary_key=True, index=True)
    revision_unitaria_id = Column(
        BigInteger,
        ForeignKey("revision_unitaria.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    nombre_archivo = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)

    tipo = Column(
        SAEnum(TipoImagen, name="tipo_imagen", native_enum=True),
        nullable=True,
        server_default=TipoImagen.otro.value,
    )

    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=True)

    revision_unitaria = relationship("RevisionUnitaria", back_populates="imagenes")


class Trabajador(Base):
    __tablename__ = "trabajador"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)

    dni = Column(String(20), unique=True, nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)

    fecha_ingreso = Column(Date, nullable=True)
    puesto = Column(String(50), nullable=True)

    activo = Column(Boolean, nullable=True, server_default="true")
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=True)

    revisiones = relationship(
        "Revision",
        secondary=revision_trabajador,
        back_populates="trabajadores",
    )
