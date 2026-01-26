from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import io, zipfile
import requests
import numpy as np
import cv2
import zxingcpp
from typing import List, Optional

router = APIRouter(prefix="/imagenes", tags=["Imagenes"])

# ----------------------------
# CONFIGURACIÓN
# ----------------------------
DEBUG_SAVE = True
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILES = 1200
MAX_TOTAL_UNCOMPRESSED = 2_000_000_000
MAX_SINGLE_FILE_UNCOMPRESSED = 25_000_000
MAX_ZIP_SIZE = 2_000_000_000
BATCH_SIZE = 400  # Procesar en lotes de 400

# URL del Worker
WORKER_UPLOAD_URL = "https://floral-dawn-a37d.omarhgd34.workers.dev"

# ----------------------------
# FUNCIONES AUXILIARES
# ----------------------------
def _is_allowed(name: str) -> bool:
    return any(name.lower().endswith(ext) for ext in ALLOWED_EXTS)

def _decode_qr_from_bytes(img_bytes: bytes) -> List[str]:
    np_img = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img is None:
        return []
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = zxingcpp.read_barcodes(img_rgb)
    return [r.text for r in results if r.text]

def upload_to_worker(filename: str, img_bytes: bytes, folder: Optional[str] = None) -> str:
    """
    Envía la imagen al Worker y obtiene el 'key' (ruta con carpeta) donde se guardó en R2.
    """
    files = {"file": (filename, img_bytes, "image/jpeg")}
    data = {"carpeta": folder} if folder else {}

    try:
        resp = requests.post(WORKER_UPLOAD_URL, files=files, data=data, timeout=60)
        resp.raise_for_status()
        return resp.json().get("key", "")
    except Exception as e:
        print(f"Error subiendo {filename} al worker:", e)
        return ""

# ----------------------------
# ENDPOINT PRINCIPAL
# ----------------------------
@router.post("/leer-qr-zip")
async def leer_qr_zip(
    file: UploadFile = File(...),
    revision_id: int = Form(...)
):
    """
    Procesa un ZIP de imágenes, detecta QR y las sube a R2 en la carpeta:
    revisiones/revisiones_imgs/revision_{revision_id}/
    """
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Debe subir un archivo ZIP")

    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=413, detail="ZIP demasiado grande")

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="ZIP inválido")

    infos = [i for i in zf.infolist() if not i.is_dir()]
    if not infos:
        raise HTTPException(status_code=400, detail="ZIP vacío")
    if len(infos) > MAX_FILES:
        raise HTTPException(status_code=413, detail="Demasiados archivos")
    if sum(i.file_size for i in infos) > MAX_TOTAL_UNCOMPRESSED:
        raise HTTPException(status_code=413, detail="Contenido descomprimido demasiado grande")

    resultados = []
    leidas = omitidas = errores = 0

    # Carpeta dinámica para R2 según el ID de la revisión
    carpeta_revision = f"revisiones/revisiones_imgs/revision_{revision_id}"

    # ----------------------------
    # Procesar en lotes de BATCH_SIZE
    # ----------------------------
    for i in range(0, len(infos), BATCH_SIZE):
        lote = infos[i:i+BATCH_SIZE]

        for info in lote:
            name = info.filename

            if not _is_allowed(name):
                omitidas += 1
                continue

            if info.file_size > MAX_SINGLE_FILE_UNCOMPRESSED:
                errores += 1
                resultados.append({
                    "archivo": name,
                    "ok": False,
                    "qr": [],
                    "error": "Imagen demasiado grande"
                })
                continue

            try:
                img_bytes = zf.read(info)

                url_key = ""
                if DEBUG_SAVE:
                    safe_name = name.replace("/", "_")
                    # Guardar en R2 dentro de la carpeta dinámica de la revisión
                    url_key = upload_to_worker(safe_name, img_bytes, folder=carpeta_revision)

                qrs = _decode_qr_from_bytes(img_bytes)

                resultados.append({
                    "archivo": name,
                    "ok": bool(qrs),
                    "qr": qrs,
                    "key_de_r2": url_key
                })
                leidas += 1

            except Exception:
                errores += 1
                resultados.append({
                    "archivo": name,
                    "ok": False,
                    "qr": [],
                    "error": "Error procesando"
                })

    return {
        "revision_id": revision_id,
        "total_archivos_en_zip": len(infos),
        "imagenes_leidas": leidas,
        "imagenes_omitidas": omitidas,
        "imagenes_con_error": errores,
        "resultados": resultados
    }
