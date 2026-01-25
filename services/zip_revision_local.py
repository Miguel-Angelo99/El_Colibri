# services/zip_revision_local.py
import shutil
import zipfile
from pathlib import Path
import re
from fastapi import HTTPException, UploadFile

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILES = 1200
MAX_TOTAL_UNCOMPRESSED = 2_000_000_000
MAX_SINGLE_FILE_UNCOMPRESSED = 25_000_000
MAX_ZIP_SIZE = 2_000_000_000

SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]")

def _is_allowed(name: str) -> bool:
    return Path(name.lower()).suffix in ALLOWED_EXTS

def _sanitize_filename(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]
    return SAFE_NAME_RE.sub("_", name)

def procesar_zip_revision_local(
    *,
    revision_id: int,
    zip_file: UploadFile,
    storage_root: str = "storage",
) -> list[dict]:
    """
    Extrae y renombra imágenes a local:
      storage/revisiones/<revision_id>/original/<...>
      storage/revisiones/<revision_id>/renamed/001.jpg ...

    Retorna:
      [{original_name, stored_name, rel_path, order_index}]
    """
    base_dir = Path(storage_root) / "revisiones" / str(revision_id)
    original_dir = base_dir / "original"
    renamed_dir = base_dir / "renamed"
    original_dir.mkdir(parents=True, exist_ok=True)
    renamed_dir.mkdir(parents=True, exist_ok=True)

    tmp_zip_path = base_dir / "upload.zip"
    try:
        with tmp_zip_path.open("wb") as f:
            shutil.copyfileobj(zip_file.file, f)
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo guardar el ZIP")

    if tmp_zip_path.stat().st_size > MAX_ZIP_SIZE:
        raise HTTPException(status_code=413, detail="ZIP demasiado grande")

    zf = None
    try:
        try:
            zf = zipfile.ZipFile(tmp_zip_path)
        except Exception:
            raise HTTPException(status_code=400, detail="ZIP inválido o corrupto")

        infos = [i for i in zf.infolist() if not i.is_dir()]
        if not infos:
            raise HTTPException(status_code=400, detail="ZIP vacío")
        if len(infos) > MAX_FILES:
            raise HTTPException(status_code=413, detail=f"Demasiados archivos (max {MAX_FILES})")

        total_uncompressed = sum(i.file_size for i in infos)
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
            raise HTTPException(status_code=413, detail="El contenido descomprimido excede el límite")

        imgs = []
        for info in infos:
            if not _is_allowed(info.filename):
                continue
            if info.file_size > MAX_SINGLE_FILE_UNCOMPRESSED:
                raise HTTPException(status_code=413, detail=f"Imagen demasiado grande: {info.filename}")
            imgs.append(info)

        if not imgs:
            raise HTTPException(status_code=400, detail="No hay imágenes válidas dentro del ZIP")

        imgs.sort(key=lambda x: x.filename)

        extracted = []
        for info in imgs:
            safe_name = _sanitize_filename(info.filename)
            target = original_dir / safe_name
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append((safe_name, target))

        n = len(extracted)
        pad = max(3, len(str(n)))

        results = []
        for idx, (orig_name, orig_path) in enumerate(extracted, start=1):
            ext = orig_path.suffix.lower()
            stored_name = f"{idx:0{pad}d}{ext}"
            stored_path = renamed_dir / stored_name
            shutil.copy2(orig_path, stored_path)

            rel_path = str(Path("revisiones") / str(revision_id) / "renamed" / stored_name).replace("\\", "/")
            results.append({
                "original_name": orig_name,
                "stored_name": stored_name,
                "rel_path": rel_path,
                "order_index": idx,
            })

        return results

    finally:
        try:
            if zf:
                zf.close()
        except Exception:
            pass
        try:
            tmp_zip_path.unlink(missing_ok=True)
        except Exception:
            pass
