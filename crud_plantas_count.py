# crud_plantas_count.py
from sqlalchemy.orm import Session

# Ajusta el import si tu clase no se llama Planta
from plantas import Planta  # si tu modelo está en plantas.py

def contar_plantas_por_sector(db: Session, sector_id: int) -> int:
    return db.query(Planta).filter(Planta.sector_id == sector_id).count()
