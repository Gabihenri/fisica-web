import secrets
import string
from typing import Any, Dict, Optional

from db import get_supabase_client


CODIGO_ALFABETO = string.ascii_uppercase + string.digits


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def gerar_codigo_ambiente() -> str:
    return "FIS-" + "".join(secrets.choice(CODIGO_ALFABETO) for _ in range(4))


def criar_ambiente_compartilhado(user_id: str, titulo: str, experimento: str, turma_id: str = "", professor_responsavel: str = "") -> Dict[str, Any]:
    user_id = _texto(user_id)
    titulo = _texto(titulo) or "Ambiente Experimental"
    experimento = _texto(experimento)
    if not user_id:
        raise PermissionError("Faça login para criar um ambiente.")
    tipos = {
        "queda": ("Queda Livre", "queda_livre"),
        "pendulo": ("Pêndulo Simples", "pendulo_simples"),
        "plano": ("Plano Inclinado", "plano_inclinado"),
    }
    if experimento not in tipos:
        raise ValueError("Experimento inválido.")
    client = get_supabase_client()

    if not turma_id:
        raise ValueError("Selecione uma turma para criar o ambiente.")

    codigo = gerar_codigo_ambiente()
    while client.table("grupos_experimentais").select("id").eq("codigo_grupo", codigo).limit(1).execute().data:
        codigo = gerar_codigo_ambiente()

    grupo = client.table("grupos_experimentais").insert({
        "turma_id": turma_id,
        "codigo_grupo": codigo,
        "professor_responsavel": _texto(professor_responsavel) or None,
        "quantidade_participantes": 0,
        "owner_user_id": user_id,
    }).execute().data
    grupo = grupo[0] if grupo else None
    if not grupo:
        raise RuntimeError("Não foi possível criar o ambiente.")

    client.table("usuarios_grupos").upsert({
        "user_id": user_id,
        "grupo_id": grupo["id"],
        "papel": "professor",
        "ativo": True,
    }, on_conflict="user_id,grupo_id").execute()

    client.table("experimentos").insert({
        "grupo_id": grupo["id"],
        "tipo": tipos[experimento][1],
        "titulo": titulo,
        "status": "em_andamento",
        "modo_aquisicao": "manual",
    }).execute()

    return {"grupo": grupo, "codigo": codigo, "titulo": titulo, "experimento": tipos[experimento][0]}


def entrar_ambiente_por_codigo(user_id: str, codigo: str) -> Dict[str, Any]:
    user_id = _texto(user_id)
    codigo = _texto(codigo).upper().replace(" ", "")
    if not user_id:
        raise PermissionError("Faça login para entrar em um ambiente.")
    if not codigo:
        raise ValueError("Informe o código do ambiente.")

    client = get_supabase_client()
    grupo_rows = client.table("grupos_experimentais").select("*").eq("codigo_grupo", codigo).limit(1).execute().data or []
    grupo = grupo_rows[0] if grupo_rows else None
    if not grupo:
        raise LookupError("Código de ambiente não encontrado.")

    client.table("usuarios_grupos").upsert({
        "user_id": user_id,
        "grupo_id": grupo["id"],
        "papel": "estudante",
        "ativo": True,
    }, on_conflict="user_id,grupo_id").execute()

    turma_rows = client.table("turmas").select("*").eq("id", grupo["turma_id"]).limit(1).execute().data or []
    turma = turma_rows[0] if turma_rows else None
    escola = None
    if turma:
        escola_rows = client.table("escolas").select("*").eq("id", turma["escola_id"]).limit(1).execute().data or []
        escola = escola_rows[0] if escola_rows else None

    return {"grupo": grupo, "turma": turma, "escola": escola}


def listar_turmas_para_ambiente(user_id: str):
    user_id = _texto(user_id)
    if not user_id:
        return []
    client = get_supabase_client()
    vinculos = client.table("usuarios_turmas").select("turma_id,papel").eq("user_id", user_id).eq("ativo", True).eq("papel", "professor").execute().data or []
    resultado = []
    for item in vinculos:
        turma_rows = client.table("turmas").select("*").eq("id", item["turma_id"]).limit(1).execute().data or []
        if turma_rows:
            turma = turma_rows[0]
            escola_rows = client.table("escolas").select("nome").eq("id", turma["escola_id"]).limit(1).execute().data or []
            turma["escola_nome"] = escola_rows[0]["nome"] if escola_rows else ""
            resultado.append(turma)
    return resultado
