from datetime import date
from typing import Any, Dict, Optional

from db import get_supabase_client


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _primeiro(dados: Any) -> Optional[Dict[str, Any]]:
    return dados[0] if isinstance(dados, list) and dados else None


def cadastrar_somente_contexto_escolar(payload: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Cria/reutiliza apenas escola e turma; não cria grupo experimental."""
    user_id = _texto(user_id)
    if not user_id:
        raise PermissionError("Faça login antes de cadastrar o contexto escolar.")

    escola_nome = _texto(payload.get("escola"))
    serie = _texto(payload.get("serie"))
    turma_nome = _texto(payload.get("turma"))
    if not escola_nome:
        raise ValueError("Informe o nome da escola.")
    if not serie:
        raise ValueError("Informe a série/ano.")
    if not turma_nome:
        raise ValueError("Informe a turma.")

    client = get_supabase_client()
    municipio = _texto(payload.get("municipio"))
    estado = _texto(payload.get("estado")).upper()
    rede = _texto(payload.get("rede"))

    consulta = client.table("escolas").select("*").eq("nome", escola_nome)
    if municipio:
        consulta = consulta.eq("municipio", municipio)
    if estado:
        consulta = consulta.eq("estado", estado)
    escola = _primeiro(consulta.limit(1).execute().data)
    if not escola:
        escola = _primeiro(client.table("escolas").insert({
            "nome": escola_nome,
            "rede": rede or None,
            "municipio": municipio or None,
            "estado": estado or None,
        }).execute().data)
    if not escola:
        raise RuntimeError("Não foi possível salvar a escola.")

    ano_letivo = int(payload.get("ano_letivo") or date.today().year)
    consulta_turma = client.table("turmas").select("*").eq("escola_id", escola["id"]).eq("ano_letivo", ano_letivo).eq("serie_ano", serie).eq("turma", turma_nome)
    turma = _primeiro(consulta_turma.limit(1).execute().data)
    if not turma:
        turma = _primeiro(client.table("turmas").insert({
            "escola_id": escola["id"],
            "ano_letivo": ano_letivo,
            "serie_ano": serie,
            "turma": turma_nome,
            "turno": _texto(payload.get("turno")) or None,
            "componente_curricular": _texto(payload.get("componente_curricular")) or "Física",
            "professor_responsavel": _texto(payload.get("professor_responsavel")) or None,
        }).execute().data)
    if not turma:
        raise RuntimeError("Não foi possível salvar a turma.")

    client.table("usuarios_instituicoes").upsert({
        "user_id": user_id,
        "escola_id": escola["id"],
        "papel": "professor",
        "ativo": True,
    }, on_conflict="user_id,escola_id").execute()
    client.table("usuarios_turmas").upsert({
        "user_id": user_id,
        "turma_id": turma["id"],
        "papel": "professor",
        "ativo": True,
    }, on_conflict="user_id,turma_id").execute()

    return {"escola": escola, "turma": turma}
