import os
from fastapi import Header, HTTPException, status, Request

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY no está definida en variables de Railway")


def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    # ✅ Permitir preflight CORS
    if request.method == "OPTIONS":
        return True

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o faltante",
        )

    return True
