import os
from typing import Any, Dict

from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

_client: Client | None = None


def get_supabase_client() -> Client:
    """Cria e reutiliza o cliente Supabase do backend.

    As credenciais devem existir apenas como variáveis de ambiente do servidor.
    Nenhuma chave é registrada em log ou retornada ao navegador.
    """
    global _client

    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL não configurada no ambiente.")

    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_KEY não configurada no ambiente.")

    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _client


def verificar_conexao_supabase() -> Dict[str, Any]:
    """Executa uma consulta somente de leitura na tabela `escolas`.

    Este teste não cria, altera nem remove registros. Serve apenas para validar:
    - variáveis de ambiente;
    - inicialização do cliente;
    - comunicação Render -> Supabase;
    - existência/acesso à tabela `escolas`.
    """
    try:
        client = get_supabase_client()
        resposta = client.table("escolas").select("id,nome").limit(1).execute()
        dados = resposta.data or []

        return {
            "ok": True,
            "servico": "supabase",
            "tabela": "escolas",
            "mensagem": "Conexão com o Supabase estabelecida com sucesso.",
            "registros_retornados": len(dados),
        }
    except Exception as exc:
        return {
            "ok": False,
            "servico": "supabase",
            "tabela": "escolas",
            "mensagem": "Falha ao conectar ao Supabase.",
            "erro": str(exc),
        }
