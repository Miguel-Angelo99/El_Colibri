from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2
import zxingcpp

router = APIRouter(prefix="/imagenes", tags=["Imagenes"])

@router.post("/leer-qr")
async def leer_qr(file: UploadFile = File(...)):
    # leer archivo
    content = await file.read()

    # bytes -> numpy -> imagen
    np_img = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Imagen inválida o no se pudo decodificar")

    # ZXing trabaja mejor en RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # leer códigos (QR, DataMatrix, etc)
    results = zxingcpp.read_barcodes(img_rgb)

    if not results:
        return {
            "qr_detectado": False,
            "valores": []
        }

    valores = [r.text for r in results if r.text]

    return {
        "qr_detectado": bool(valores),
        "valores": valores
    }
