from fastapi import APIRouter, UploadFile, File, HTTPException
import numpy as np
import cv2
import zxingcpp

router = APIRouter(prefix="/imagenes", tags=["Imagenes"])


def _try_decode(img_bgr: np.ndarray):
    """
    Devuelve lista de textos detectados por zxingcpp, o [].
    Reintenta con varias transformaciones para aumentar tasa de lectura.
    """
    attempts = []

    # 1) Original en RGB
    attempts.append(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

    # 2) Gris -> RGB
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    attempts.append(cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB))

    # 3) CLAHE (mejora contraste) -> RGB
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    attempts.append(cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB))

    # 4) Binarizado Otsu -> RGB
    _, th = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    attempts.append(cv2.cvtColor(th, cv2.COLOR_GRAY2RGB))

    # 5) Sharpen ligero -> RGB (ayuda si está un poco borroso)
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]], dtype=np.float32)
    sharp = cv2.filter2D(img_bgr, -1, kernel)
    attempts.append(cv2.cvtColor(sharp, cv2.COLOR_BGR2RGB))

    # Reintento multi-escala
    scales = [1.0, 1.5, 2.0, 3.0]

    for base in attempts:
        for s in scales:
            if s != 1.0:
                h, w = base.shape[:2]
                resized = cv2.resize(base, (int(w * s), int(h * s)), interpolation=cv2.INTER_CUBIC)
            else:
                resized = base

            results = zxingcpp.read_barcodes(resized)
            textos = [r.text for r in results if r.text]
            if textos:
                return textos

    return []


@router.post("/leer-qr")
async def leer_qr(file: UploadFile = File(...)):
    content = await file.read()
    np_img = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Imagen inválida o no se pudo decodificar")

    textos = _try_decode(img)

    # Diagnóstico simple: tamaño de la imagen (para saber si estás mandando algo gigante o muy comprimido)
    h, w = img.shape[:2]

    return {
        "qr_detectado": bool(textos),
        "valores": textos,
        "debug": {
            "width": w,
            "height": h
        }
    }
