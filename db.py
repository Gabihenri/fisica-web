import os
from datetime import date
from typing import Any, Dict, List, Optional

from flask import has_request_context, session
from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

_client: Client | None = None

TIPOS_EXPERIMENTO = {
    "queda": ("queda_livre", "Queda Livre"),
    "pendulo": ("pendulo_simples", "Pêndulo Simples"),
    "plano": ("plano_inclinado", "Plano Inclinado"),
}


def get_supabase_client() -> Client:
    global _client
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL não configurada no ambiente.")
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY não configurada no ambiente.")
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def verificar_conexao_supabase() -> Dict[str, Any]:
    try:
        client = get_supabase_client()
        resposta = client.table("escolas").select("id,nome").limit(1).execute()
        dados = resposta.data or []
        return {"ok": True, "servico": "supabase", "tabela": "escolas", "mensagem": "Conexão com o Supabase estabelecida com sucesso.", "registros_retornados": len(dados)}
    except Exception as exc:
        return {"ok": False, "servico": "supabase", "tabela": "escolas", "mensagem": "Falha ao conectar ao Supabase.", "erro": str(exc)}


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _primeiro(dados: Any) -> Optional[Dict[str, Any]]:
    if isinstance(dados, list) and dados:
        return dados[0]
    return None


def _usuario_sessao_id() -> str:
    if not has_request_context():
        return ""
    return _texto(session.get("user_id"))


def registrar_perfil_usuario(user_id: str, nome: str, papel: str = "professor") -> None:
    user_id = _texto(user_id)
    if not user_id:
        return
    papel = _texto(papel).lower()
    if papel not in {"professor", "estudante"}:
        papel = "professor"
    get_supabase_client().table("perfis_acesso").upsert(
        {"user_id": user_id, "nome": _texto(nome) or None, "papel": papel, "ativo": True},
        on_conflict="user_id",
    ).execute()


def _vincular_usuario_contexto(user_id: str, escola_id: str, turma_id: str, grupo_id: str, papel: str = "professor") -> None:
    user_id = _texto(user_id)
    if not user_id:
        return
    client = get_supabase_client()
    papel_grupo = "professor" if papel == "professor" else "estudante"
    papel_instituicao = "professor" if papel == "professor" else "estudante"
    client.table("usuarios_instituicoes").upsert(
        {"user_id": user_id, "escola_id": escola_id, "papel": papel_instituicao, "ativo": True},
        on_conflict="user_id,escola_id",
    ).execute()
    client.table("usuarios_turmas").upsert(
        {"user_id": user_id, "turma_id": turma_id, "papel": papel_grupo, "ativo": True},
        on_conflict="user_id,turma_id",
    ).execute()
    client.table("usuarios_grupos").upsert(
        {"user_id": user_id, "grupo_id": grupo_id, "papel": papel_grupo, "ativo": True},
        on_conflict="user_id,grupo_id",
    ).execute()


def usuario_tem_acesso_grupo(user_id: str, grupo_id: str) -> bool:
    user_id = _texto(user_id)
    grupo_id = _texto(grupo_id)
    if not user_id or not grupo_id:
        return False
    dados = get_supabase_client().table("usuarios_grupos").select("user_id").eq("user_id", user_id).eq("grupo_id", grupo_id).eq("ativo", True).limit(1).execute().data or []
    return bool(dados)


def _garantir_acesso_grupo(grupo_id: str) -> None:
    if not has_request_context():
        return
    user_id = _usuario_sessao_id()
    if not user_id:
        raise PermissionError("Faça login para acessar este grupo.")
    if not usuario_tem_acesso_grupo(user_id, grupo_id):
        raise PermissionError("Este grupo não pertence ao seu acesso.")


def listar_grupos_usuario(user_id: str) -> List[Dict[str, Any]]:
    user_id = _texto(user_id)
    if not user_id:
        return []
    client = get_supabase_client()
    vinculos = client.table("usuarios_grupos").select("grupo_id,papel").eq("user_id", user_id).eq("ativo", True).execute().data or []
    saida = []
    for vinculo in vinculos:
        gid = vinculo.get("grupo_id")
        grupo = _primeiro(client.table("grupos_experimentais").select("*").eq("id", gid).limit(1).execute().data)
        if not grupo:
            continue
        turma = _primeiro(client.table("turmas").select("*").eq("id", grupo["turma_id"]).limit(1).execute().data)
        escola = _primeiro(client.table("escolas").select("*").eq("id", turma["escola_id"]).limit(1).execute().data) if turma else None
        saida.append({"grupo": grupo, "turma": turma, "escola": escola, "papel": vinculo.get("papel")})
    return saida


def obter_ou_criar_escola(nome: str, rede: str = "", municipio: str = "", estado: str = "") -> Dict[str, Any]:
    client = get_supabase_client(); nome = _texto(nome)
    if not nome: raise ValueError("Informe o nome da escola.")
    consulta = client.table("escolas").select("*").eq("nome", nome)
    if _texto(municipio): consulta = consulta.eq("municipio", _texto(municipio))
    if _texto(estado): consulta = consulta.eq("estado", _texto(estado).upper())
    existente = _primeiro(consulta.limit(1).execute().data)
    if existente: return existente
    payload = {"nome": nome, "rede": _texto(rede) or None, "municipio": _texto(municipio) or None, "estado": _texto(estado).upper() or None}
    return _primeiro(client.table("escolas").insert(payload).execute().data) or payload


def obter_ou_criar_turma(escola_id: str, ano_letivo: int, serie_ano: str, turma: str, turno: str = "", componente_curricular: str = "Física", professor_responsavel: str = "") -> Dict[str, Any]:
    client = get_supabase_client(); serie_ano = _texto(serie_ano); turma = _texto(turma)
    if not serie_ano or not turma: raise ValueError("Informe série/ano e turma.")
    existente = _primeiro(client.table("turmas").select("*").eq("escola_id", escola_id).eq("ano_letivo", int(ano_letivo)).eq("serie_ano", serie_ano).eq("turma", turma).limit(1).execute().data)
    if existente: return existente
    payload = {"escola_id": escola_id, "ano_letivo": int(ano_letivo), "serie_ano": serie_ano, "turma": turma, "turno": _texto(turno) or None, "componente_curricular": _texto(componente_curricular) or "Física", "professor_responsavel": _texto(professor_responsavel) or None}
    return _primeiro(client.table("turmas").insert(payload).execute().data) or payload


def obter_ou_criar_grupo(turma_id: str, codigo_grupo: str, professor_responsavel: str = "", quantidade_participantes: int = 0, data_experimento: Optional[str] = None) -> Dict[str, Any]:
    client = get_supabase_client(); codigo_grupo = _texto(codigo_grupo) or "Grupo 1"; data_experimento = data_experimento or date.today().isoformat()
    existente = _primeiro(client.table("grupos_experimentais").select("*").eq("turma_id", turma_id).eq("codigo_grupo", codigo_grupo).eq("data_experimento", data_experimento).limit(1).execute().data)
    if existente: return existente
    payload = {"turma_id": turma_id, "codigo_grupo": codigo_grupo, "data_experimento": data_experimento, "professor_responsavel": _texto(professor_responsavel) or None, "quantidade_participantes": max(int(quantidade_participantes or 0), 0)}
    return _primeiro(client.table("grupos_experimentais").insert(payload).execute().data) or payload


def salvar_participantes(grupo_id: str, nomes: List[str]) -> List[Dict[str, Any]]:
    client = get_supabase_client(); salvos=[]; nomes_validos=[_texto(nome) for nome in nomes if _texto(nome)]
    for indice,nome in enumerate(nomes_validos,start=1):
        codigo=f"P{indice:02d}"; existente=_primeiro(client.table("participantes").select("*").eq("grupo_id",grupo_id).eq("codigo_participante",codigo).limit(1).execute().data)
        if existente:
            atualizado=client.table("participantes").update({"nome_exibicao":nome}).eq("id",existente["id"]).execute().data; salvos.append(_primeiro(atualizado) or existente)
        else:
            payload={"grupo_id":grupo_id,"codigo_participante":codigo,"nome_exibicao":nome}; salvos.append(_primeiro(client.table("participantes").insert(payload).execute().data) or payload)
    return salvos


def cadastrar_contexto_escolar(payload: Dict[str, Any]) -> Dict[str, Any]:
    nomes=payload.get("nomes") or []; escola=obter_ou_criar_escola(payload.get("escola",""),payload.get("rede",""),payload.get("municipio",""),payload.get("estado",""))
    turma=obter_ou_criar_turma(escola["id"],int(payload.get("ano_letivo") or date.today().year),payload.get("serie",""),payload.get("turma",""),payload.get("turno",""),payload.get("componente_curricular","Física"),payload.get("professor_responsavel",""))
    grupo=obter_ou_criar_grupo(turma["id"],payload.get("codigo_grupo","Grupo 1"),payload.get("professor_responsavel",""),len([n for n in nomes if _texto(n)]))
    participantes=salvar_participantes(grupo["id"],nomes)
    user_id = _usuario_sessao_id()
    if user_id:
        _vincular_usuario_contexto(user_id, escola["id"], turma["id"], grupo["id"], "professor")
    return {"escola":escola,"turma":turma,"grupo":grupo,"participantes":participantes}


def obter_contexto_grupo(grupo_id: str) -> Optional[Dict[str, Any]]:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client(); grupo=_primeiro(client.table("grupos_experimentais").select("*").eq("id",grupo_id).limit(1).execute().data)
    if not grupo:return None
    turma=_primeiro(client.table("turmas").select("*").eq("id",grupo["turma_id"]).limit(1).execute().data); escola=_primeiro(client.table("escolas").select("*").eq("id",turma["escola_id"]).limit(1).execute().data) if turma else None
    participantes=client.table("participantes").select("*").eq("grupo_id",grupo_id).order("codigo_participante").execute().data or []
    return {"grupo":grupo,"turma":turma,"escola":escola,"participantes":participantes}


def obter_ou_criar_experimento(grupo_id: str, chave_experimento: str) -> Dict[str, Any]:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client()
    if chave_experimento not in TIPOS_EXPERIMENTO: raise ValueError("Experimento inválido.")
    tipo,titulo=TIPOS_EXPERIMENTO[chave_experimento]; existente=_primeiro(client.table("experimentos").select("*").eq("grupo_id",grupo_id).eq("tipo",tipo).eq("status","em_andamento").order("created_at",desc=True).limit(1).execute().data)
    if existente:return existente
    payload={"grupo_id":grupo_id,"tipo":tipo,"titulo":titulo,"status":"em_andamento","modo_aquisicao":"manual"}; return _primeiro(client.table("experimentos").insert(payload).execute().data) or payload


def registrar_medicao(grupo_id: str, chave_experimento: str, valores: Dict[str, Any], origem: str = "manual") -> Dict[str, Any]:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client(); experimento=obter_ou_criar_experimento(grupo_id,chave_experimento); existentes=client.table("medicoes").select("numero_medicao").eq("experimento_id",experimento["id"]).order("numero_medicao",desc=True).limit(1).execute().data or []
    proximo=int(existentes[0]["numero_medicao"])+1 if existentes else 1; payload={"experimento_id":experimento["id"],"numero_medicao":proximo,"origem":origem,**valores}; medicao=_primeiro(client.table("medicoes").insert(payload).execute().data) or payload
    return {"experimento":experimento,"medicao":medicao}


def listar_medicoes(grupo_id: str, chave_experimento: str) -> List[Dict[str, Any]]:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client()
    if chave_experimento not in TIPOS_EXPERIMENTO:return []
    tipo,_=TIPOS_EXPERIMENTO[chave_experimento]; experimento=_primeiro(client.table("experimentos").select("id").eq("grupo_id",grupo_id).eq("tipo",tipo).order("created_at",desc=True).limit(1).execute().data)
    if not experimento:return []
    return client.table("medicoes").select("*").eq("experimento_id",experimento["id"]).order("numero_medicao").execute().data or []


def salvar_resultado(grupo_id: str, chave_experimento: str, estatisticas: Dict[str, Any], interpretacao: str) -> None:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client(); experimento=obter_ou_criar_experimento(grupo_id,chave_experimento)
    payload={"experimento_id":experimento["id"],"numero_medidas":int(estatisticas.get("n") or 0),"gravidade_referencia":estatisticas.get("gravidade_referencia") or 9.80665,"media_gravidade":estatisticas.get("media"),"desvio_padrao":estatisticas.get("desvio_padrao"),"erro_percentual":estatisticas.get("erro_percentual"),"valor_minimo":estatisticas.get("minimo"),"valor_maximo":estatisticas.get("maximo"),"classificacao_qualidade":estatisticas.get("qualidade"),"interpretacao":interpretacao}
    client.table("resultados_experimentais").upsert(payload,on_conflict="experimento_id").execute()


def salvar_relatorio(grupo_id: str, chave_experimento: str, tipo_relatorio: str, resumo: str, parecer_pedagogico: str, audiodescricao: str, descricao_grafico: str, versao: int = 1) -> Dict[str, Any]:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client(); experimento=obter_ou_criar_experimento(grupo_id,chave_experimento)
    payload={"experimento_id":experimento["id"],"tipo_relatorio":_texto(tipo_relatorio) or "experimental","resumo":_texto(resumo) or None,"parecer_pedagogico":_texto(parecer_pedagogico) or None,"audiodescricao":_texto(audiodescricao) or None,"descricao_grafico":_texto(descricao_grafico) or None,"versao":max(int(versao or 1),1)}
    resposta=client.table("relatorios").upsert(payload,on_conflict="experimento_id,tipo_relatorio,versao").execute(); return _primeiro(resposta.data) or payload


def limpar_medicoes(grupo_id: str, chave_experimento: str) -> None:
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client()
    if chave_experimento not in TIPOS_EXPERIMENTO:return
    tipo,_=TIPOS_EXPERIMENTO[chave_experimento]; experimento=_primeiro(client.table("experimentos").select("id").eq("grupo_id",grupo_id).eq("tipo",tipo).order("created_at",desc=True).limit(1).execute().data)
    if not experimento:return
    client.table("medicoes").delete().eq("experimento_id",experimento["id"]).execute(); client.table("resultados_experimentais").delete().eq("experimento_id",experimento["id"]).execute(); client.table("relatorios").delete().eq("experimento_id",experimento["id"]).execute()


def excluir_grupo_experimental(grupo_id: str) -> None:
    """Exclui um grupo e seus dados dependentes sem apagar escola ou turma."""
    _garantir_acesso_grupo(grupo_id)
    client=get_supabase_client(); grupo_id=_texto(grupo_id)
    if not grupo_id: raise ValueError("Grupo não informado.")
    experimentos=client.table("experimentos").select("id").eq("grupo_id",grupo_id).execute().data or []
    for experimento in experimentos:
        eid=experimento.get("id")
        if not eid: continue
        client.table("medicoes").delete().eq("experimento_id",eid).execute()
        client.table("resultados_experimentais").delete().eq("experimento_id",eid).execute()
        client.table("relatorios").delete().eq("experimento_id",eid).execute()
    client.table("experimentos").delete().eq("grupo_id",grupo_id).execute()
    client.table("participantes").delete().eq("grupo_id",grupo_id).execute()
    client.table("usuarios_grupos").delete().eq("grupo_id",grupo_id).execute()
    client.table("grupos_experimentais").delete().eq("id",grupo_id).execute()
