# services/zip_processor.py
import shutil
import zipfile
from pathlib import Path
import re
from fastapi import HTTPException, UploadFile

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]")

def _sanitize_filename(name: str) -> str:
    name = name.replace("\\", "/").split("/")[-1]
    return SAFE_NAME_RE.sub("_", name)

def _is_image(name: str) -> bool:
    return Path(name).suffix.lower() in IMAGE_EXTS

def procesar_zip_revision_local(
    *,
    revision_id: int,
    zip_file: UploadFile,
    storage_root: str = "storage",
    expected_count: int | None = None,
) -> list[dict]:
    """
    Devuelve lista:
    [{original_name, stored_name, rel_path, order_index}]
    """
    base_dir = Path(storage_root) / "revisiones" / str(revision_id)
    original_dir = base_dir / "original"
    renamed_dir = base_dir / "renamed"
    original_dir.mkdir(parents=True, exist_ok=True)
    renamed_dir.mkdir(parents=True, exist_ok=True)

    tmp_zip_path = base_dir / "upload.zip"
    with tmp_zip_path.open("wb") as f:
        shutil.copyfileobj(zip_file.file, f)

    try:
        with zipfile.ZipFile(tmp_zip_path) as z:
            members = [m for m in z.infolist() if not m.is_dir()]
            imgs = [m for m in members if _is_image(m.filename)]

            if not imgs:
                raise HTTPException(400, "El ZIP no contiene imágenes válidas.")

            if expected_count is not None and len(imgs) != expected_count:
                raise HTTPException(
                    400,
                    f"Cantidad de fotos inválida. ZIP={len(imgs)} vs expected={expected_count}."
                )

            extracted: list[tuple[str, Path]] = []
            for m in imgs:
                safe_name = _sanitize_filename(m.filename)
                target = original_dir / safe_name
                with z.open(m) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted.append((safe_name, target))

        extracted.sort(key=lambda x: x[0].lower())
        n = len(extracted)
        pad = max(3, len(str(n)))

        results: list[dict] = []
        for idx, (orig_name, orig_path) in enumerate(extracted, start=1):
            ext = orig_path.suffix.lower()
            new_name = f"{idx:0{pad}d}{ext}"
            new_path = renamed_dir / new_name
            shutil.copy2(orig_path, new_path)

            rel_path = str(Path("revisiones") / str(revision_id) / "renamed" / new_name).replace("\\", "/")
            results.append({
                "original_name": orig_name,
                "stored_name": new_name,
                "rel_path": rel_path,
                "order_index": idx,
            })

        return results
    finally:
        try:
            tmp_zip_path.unlink(missing_ok=True)
        except:
            pass
