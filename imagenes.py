from fastapi import APIRouter, UploadFile, File, HTTPException
import io
import numpy as np
import cv2
import zxingcpp
import zipfile
from pathlib import Path

router = APIRouter(prefix="/imagenes", tags=["Imagenes"])

# ------------------------
# CONFIG DEBUG LOCAL
# ------------------------
DEBUG_SAVE = True  # ⚠️ poner False en producción
DEBUG_DIR = Path("storage/debug_qr")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------
# CONFIG SEGURIDAD / LÍMITES
# ------------------------
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILES = 1200
MAX_TOTAL_UNCOMPRESSED = 2_000_000_000      # 2GB
MAX_SINGLE_FILE_UNCOMPRESSED = 25_000_000   # 25MB
MAX_ZIP_SIZE = 2_000_000_000                # 2GB

# ------------------------
# HELPERS
# ------------------------
def _is_allowed(name: str) -> bool:
    n = name.lower()
    return any(n.endswith(ext) for ext in ALLOWED_EXTS)

def _decode_qr_from_bytes(img_bytes: bytes) -> list[str]:
    np_img = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img is None:
        return []

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = zxingcpp.read_barcodes(img_rgb)
    return [r.text for r in results if r.text]

# ------------------------
# ENDPOINT
# ------------------------
@router.post("/leer-qr-zip")
async def leer_qr_zip(file: UploadFile = File(...)):
    # 1️⃣ Validar ZIP
    filename = (file.filename or "").lower()
    if not filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .zip")

    # 2️⃣ Leer ZIP en memoria
    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=413, detail="ZIP demasiado grande")

    # 3️⃣ Abrir ZIP
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="ZIP inválido o corrupto")

    infos = [i for i in zf.infolist() if not i.is_dir()]

    if not infos:
        raise HTTPException(status_code=400, detail="ZIP vacío")
    if len(infos) > MAX_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Demasiados archivos en el ZIP (max {MAX_FILES})"
        )

    total_uncompressed = sum(i.file_size for i in infos)
    if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
        raise HTTPException(
            status_code=413,
            detail="El contenido descomprimido excede el límite"
        )

    # ------------------------
    # PROCESAMIENTO
    # ------------------------
    resultados = []
    leidas = 0
    omitidas = 0
    errores = 0

    infos.sort(key=lambda x: x.filename)

    for info in infos:
        name = info.filename

        # Saltar archivos no permitidos
        if not _is_allowed(name):
            omitidas += 1
            continue

        if info.file_size > MAX_SINGLE_FILE_UNCOMPRESSED:
            resultados.append({
                "archivo": name,
                "qr": [],
                "ok": False,
                "error": "Imagen demasiado grande"
            })
            errores += 1
            continue

        try:
            img_bytes = zf.read(info)

            # 🟢 GUARDAR EN LOCAL (DEBUG)
            if DEBUG_SAVE:
                safe_name = name.replace("/", "_")
                with open(DEBUG_DIR / safe_name, "wb") as f:
                    f.write(img_bytes)

            qrs = _decode_qr_from_bytes(img_bytes)

            resultados.append({
                "archivo": name,
                "qr": qrs,
                "ok": bool(qrs)
            })
            leidas += 1

        except Exception:
            resultados.append({
                "archivo": name,
                "qr": [],
                "ok": False,
                "error": "No se pudo procesar"
            })
            errores += 1

    # ------------------------
    # RESPUESTA
    # ------------------------
    return {
        "total_archivos_en_zip": len(infos),
        "imagenes_leidas": leidas,
        "imagenes_omitidas": omitidas,
        "imagenes_con_error": errores,
        "resultados": resultados
    }

