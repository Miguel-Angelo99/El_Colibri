from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2
from pyzbar.pyzbar import decode

router = APIRouter(prefix="/imagenes", tags=["Imagenes"])

@router.post("/leer-qr")
async def leer_qr(file: UploadFile = File(...)):
    content = await file.read()

    np_img = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Imagen inválida o no se pudo decodificar")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # mejora de contraste (opcional pero ayuda en campo)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    qrs = decode(enhanced)

    if not qrs:
        return {"qr_detectado": False, "valores": []}

    return {
        "qr_detectado": True,
        "valores": [q.data.decode("utf-8") for q in qrs],
    }
