from fastapi import APIRouter, UploadFile, File, HTTPException
import io
import numpy as np
import cv2
import zxingcpp
import zipfile

router = APIRouter(prefix="/imagenes", tags=["Imagenes"])

# --- Config de seguridad / límites ---
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILES = 1200                     # tolera 1000 + margen
MAX_TOTAL_UNCOMPRESSED = 2_000_000_000  # 2GB descomprimido (ajusta a tu caso)
MAX_SINGLE_FILE_UNCOMPRESSED = 25_000_000  # 25MB por imagen (ajusta)
MAX_ZIP_SIZE = 2_000_000_000         # 2GB zip subido (ajusta)

def _is_allowed(name: str) -> bool:
    n = name.lower()
    return any(n.endswith(ext) for ext in ALLOWED_EXTS)

def _decode_qr_from_bytes(img_bytes: bytes) -> list[str]:
    np_img = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img is None:
        return []

    # ZXing va mejor en RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = zxingcpp.read_barcodes(img_rgb)
    return [r.text for r in results if r.text]

@router.post("/leer-qr-zip")
async def leer_qr_zip(file: UploadFile = File(...)):
    # 1) Validar tipo
    filename = (file.filename or "").lower()
    if not filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Debe subir un archivo .zip")

    # 2) Leer ZIP a memoria (para 1000 fotos puede ser pesado; si tu zip es grande, esto igual funciona,
    #    pero si esperas >500MB reales conviene pasarlo a disco temporal/worker).
    content = await file.read()

    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=413, detail="ZIP demasiado grande")

    # 3) Abrir zip y aplicar límites anti zip-bomb
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="ZIP inválido o corrupto")

    infos = [i for i in zf.infolist() if not i.is_dir()]

    if len(infos) == 0:
        raise HTTPException(status_code=400, detail="ZIP vacío")
    if len(infos) > MAX_FILES:
        raise HTTPException(status_code=413, detail=f"Demasiados archivos en el ZIP (max {MAX_FILES})")

    total_uncompressed = sum(i.file_size for i in infos)
    if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
        raise HTTPException(status_code=413, detail="El contenido descomprimido excede el límite")

    # 4) Procesar imágenes y acumular resultados
    resultados = []
    leidas = 0
    omitidas = 0
    errores = 0

    # orden estable (opcional)
    infos.sort(key=lambda x: x.filename)

    for info in infos:
        name = info.filename

        # saltar archivos raros
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
            qrs = _decode_qr_from_bytes(img_bytes)
            resultados.append({
                "archivo": name,
                "qr": qrs,
                "ok": bool(qrs)
            })
            leidas += 1
        except Exception as e:
            resultados.append({
                "archivo": name,
                "qr": [],
                "ok": False,
                "error": "No se pudo procesar"
            })
            errores += 1

    return {
        "total_archivos_en_zip": len(infos),
        "imagenes_leidas": leidas,
        "imagenes_omitidas": omitidas,
        "imagenes_con_error": errores,
        "resultados": resultados
    }
