# catalogos.py
from fastapi import APIRouter, Depends

from auth_simple import require_api_key
from models import TipoRevision

router = APIRouter(
    prefix="/catalogos",
    tags=["Catálogos"],
    dependencies=[Depends(require_api_key)],
)

@router.get("/tipos-revision")
def tipos_revision():
    # Devuelve los textos EXACTOS que espera la BD/Enum
    return {
        "items": [
            {"key": e.name, "value": e.value}
            for e in TipoRevision
        ]
    }
