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


# app.py importa este módulo depois de carregar app_core.app; nesse momento
# a aplicação Flask já existe. Registramos a API e a camada visual nova aqui,
# mantendo o núcleo de rotas existente sem substituí-lo.
try:
    from app_core import app as _app
    from observacoes import register_observation_routes
    register_observation_routes(_app)
except Exception:
    logger.exception("Não foi possível registrar as rotas de observações na inicialização")


# A aplicação já injeta participant-persistence.js. Esta camada adicional é
# inserida aqui para manter a funcionalidade modular e compatível com páginas
# existentes do laboratório.
try:
    _original_after_request_functions = list(_app.after_request_funcs.get(None, [])) if '_app' in globals() else []

    if '_app' in globals():
        @_app.after_request
        def inject_participant_observations_script(response):
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                return response
            try:
                body = response.get_data(as_text=True)
                marker = '<script src="/static/participant-observations.js" defer></script>'
                if marker not in body and "</body>" in body:
                    body = body.replace("</body>", f"{marker}</body>", 1)
                    response.set_data(body)
            except Exception:
                logger.exception("Falha ao injetar camada de observações")
            return response
except Exception:
    logger.exception("Falha ao registrar injeção da interface de observações")
