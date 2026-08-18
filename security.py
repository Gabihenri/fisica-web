import logging
import re
from functools import wraps
from typing import Any, Callable

from flask import abort, request, session
from db import get_supabase_client

logger = logging.getLogger("fisica_web.security")
ALLOWED_ROLES = {"professor", "estudante", "admin_instituicao", "admin_plataforma"}
CODE_RE = re.compile(r"^FIS-[A-Z0-9]{4}$")


def current_role(user_id: str | None = None) -> str | None:
    uid = user_id or session.get("user_id")
    if not uid:
        return None
    rows = get_supabase_client().table("perfis_acesso").select("papel,ativo").eq("user_id", uid).limit(1).execute().data or []
    if not rows or not rows[0].get("ativo"):
        return None
    role = str(rows[0].get("papel") or "").strip().lower()
    return role if role in ALLOWED_ROLES else None


def require_role(*roles: str) -> Callable:
    allowed = {r.strip().lower() for r in roles}
    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(*args: Any, **kwargs: Any):
            role = current_role()
            if role not in allowed:
                logger.warning("Acesso negado: role=%s path=%s user=%s", role, request.path, session.get("user_id"))
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def validate_environment_code(value: str) -> str:
    code = str(value or "").strip().upper().replace(" ", "")
    if not CODE_RE.fullmatch(code):
        raise ValueError("Código de ambiente inválido. Use o formato FIS-XXXX.")
    return code


def validate_text(value: str, field: str, minimum: int = 1, maximum: int = 120) -> str:
    text = str(value or "").strip()
    if not minimum <= len(text) <= maximum:
        raise ValueError(f"{field} deve ter entre {minimum} e {maximum} caracteres.")
    return text


def validate_uuid(value: str, field: str) -> str:
    import uuid
    try:
        return str(uuid.UUID(str(value or "").strip()))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{field} inválido.") from None


# app.py importa este módulo depois de carregar app_core.app; portanto,
# registramos aqui a nova API sem alterar a estrutura principal da aplicação.
try:
    from app_core import app as _app
    from observacoes import register_observation_routes
    register_observation_routes(_app)
except Exception:
    logger.exception("Não foi possível registrar as rotas de observações na inicialização")
