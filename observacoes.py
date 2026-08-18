from __future__ import annotations

from typing import Any

from flask import jsonify, request

from db import get_supabase_client, usuario_tem_acesso_grupo

TIPOS_EXPERIMENTO = {
    "queda": "queda_livre",
    "pendulo": "pendulo_simples",
    "plano": "plano_inclinado",
}


def _texto(value: Any) -> str:
    return str(value or "").strip()


def _experimento_id(grupo_id: str, chave: str) -> str | None:
    tipo = TIPOS_EXPERIMENTO.get(chave)
    if not tipo:
        return None
    rows = (
        get_supabase_client()
        .table("experimentos")
        .select("id")
        .eq("grupo_id", grupo_id)
        .eq("tipo", tipo)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
        or []
    )
    return rows[0].get("id") if rows else None


def listar_observacoes(grupo_id: str, chave: str) -> list[dict[str, Any]]:
    grupo_id = _texto(grupo_id)
    if not grupo_id or not usuario_tem_acesso_grupo(_usuario_id(), grupo_id):
        raise PermissionError("Você não pertence a este grupo.")
    experimento_id = _experimento_id(grupo_id, chave)
    if not experimento_id:
        return []
    client = get_supabase_client()
    rows = (
        client.table("observacoes_participantes")
        .select("id,participante_id,observacao,origem,created_at,updated_at")
        .eq("grupo_id", grupo_id)
        .eq("experimento_id", experimento_id)
        .order("created_at")
        .execute()
        .data
        or []
    )
    participantes = client.table("participantes").select("id,codigo_participante,nome_exibicao").eq("grupo_id", grupo_id).execute().data or []
    por_id = {str(p["id"]): p for p in participantes}
    for row in rows:
        p = por_id.get(str(row.get("participante_id")), {})
        row["codigo"] = p.get("codigo_participante", "")
        row["nome"] = p.get("nome_exibicao", "")
    return rows


def _usuario_id() -> str:
    from flask import session
    return _texto(session.get("user_id"))


def salvar_observacao(grupo_id: str, chave: str, codigo: str, observacao: str, origem: str = "escrita") -> dict[str, Any]:
    grupo_id = _texto(grupo_id)
    codigo = _texto(codigo).upper()
    observacao = _texto(observacao)
    origem = _texto(origem).lower() or "escrita"
    if not usuario_tem_acesso_grupo(_usuario_id(), grupo_id):
        raise PermissionError("Você não pertence a este grupo.")
    if chave not in TIPOS_EXPERIMENTO:
        raise ValueError("Experimento inválido.")
    if not codigo or not observacao:
        raise ValueError("Informe o participante e a observação.")
    if len(observacao) > 4000:
        raise ValueError("A observação deve ter no máximo 4000 caracteres.")
    if origem not in {"escrita", "voz_transcrita"}:
        origem = "escrita"

    client = get_supabase_client()
    participante_rows = (
        client.table("participantes")
        .select("id,codigo_participante,nome_exibicao")
        .eq("grupo_id", grupo_id)
        .eq("codigo_participante", codigo)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not participante_rows:
        raise ValueError("Participante não encontrado neste grupo.")
    participante = participante_rows[0]
    experimento_id = _experimento_id(grupo_id, chave)
    if not experimento_id:
        raise ValueError("Este experimento ainda não possui uma sessão iniciada.")

    payload = {
        "participante_id": participante["id"],
        "experimento_id": experimento_id,
        "grupo_id": grupo_id,
        "observacao": observacao,
        "origem": origem,
    }
    row = (
        client.table("observacoes_participantes")
        .upsert(payload, on_conflict="participante_id,experimento_id")
        .execute()
        .data
        or []
    )
    result = row[0] if row else payload
    result["codigo"] = participante.get("codigo_participante", codigo)
    result["nome"] = participante.get("nome_exibicao", "")
    return result


def register_observation_routes(app) -> None:
    @app.route("/api/observacoes/<experimento>", methods=["GET"])
    def api_listar_observacoes(experimento):
        grupo_id = _texto(request.args.get("grupo_id"))
        try:
            return jsonify({"observacoes": listar_observacoes(grupo_id, experimento)})
        except PermissionError as exc:
            return jsonify({"erro": str(exc), "observacoes": []}), 403
        except Exception:
            app.logger.exception("Falha ao carregar observações")
            return jsonify({"erro": "Não foi possível carregar as observações.", "observacoes": []}), 500

    @app.route("/api/observacoes/<experimento>", methods=["POST"])
    def api_salvar_observacao(experimento):
        grupo_id = _texto(request.form.get("grupo_id") or (request.get_json(silent=True) or {}).get("grupo_id"))
        data = request.get_json(silent=True) or {}
        codigo = _texto(request.form.get("codigo") or data.get("codigo"))
        observacao = _texto(request.form.get("observacao") or data.get("observacao"))
        origem = _texto(request.form.get("origem") or data.get("origem") or "escrita")
        try:
            result = salvar_observacao(grupo_id, experimento, codigo, observacao, origem)
            return jsonify({"ok": True, "observacao": result})
        except PermissionError as exc:
            return jsonify({"erro": str(exc)}), 403
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except Exception:
            app.logger.exception("Falha ao salvar observação")
            return jsonify({"erro": "Não foi possível salvar a observação."}), 500
