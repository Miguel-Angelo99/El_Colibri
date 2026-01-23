from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import SessionLocal
from auth_simple import require_api_key

from schemas import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioPasswordUpdate,
    UsuarioResponse,
)
from crud_usuarios import (
    crear_usuario,
    listar_usuarios,
    obtener_usuario,
    actualizar_usuario,
    actualizar_password,
    eliminar_usuario,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(require_api_key)],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=UsuarioResponse)
def post_usuario(body: UsuarioCreate, db: Session = Depends(get_db)):
    u, err = crear_usuario(db, body)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return u


@router.get("", response_model=list[UsuarioResponse])
def get_usuarios(
    skip: int = 0,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    return listar_usuarios(db, skip=skip, limit=limit)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    u = obtener_usuario(db, usuario_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no existe")
    return u


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def put_usuario(usuario_id: int, body: UsuarioUpdate, db: Session = Depends(get_db)):
    u, err = actualizar_usuario(db, usuario_id, body)
    if err:
        raise HTTPException(status_code=400 if "Conflicto" in err else 404, detail=err)
    return u


@router.put("/{usuario_id}/password")
def put_usuario_password(usuario_id: int, body: UsuarioPasswordUpdate, db: Session = Depends(get_db)):
    ok, err = actualizar_password(db, usuario_id, body)
    if err:
        raise HTTPException(status_code=404, detail=err)
    return {"ok": ok}


@router.delete("/{usuario_id}")
def delete_usuario(usuario_id: int, db: Session = Depends(get_db)):
    ok = eliminar_usuario(db, usuario_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuario no existe")
    return {"ok": True}
