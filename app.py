import logging
import os
import secrets

from flask import jsonify, redirect, render_template, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from supabase import create_client

from app_core import app
from ambientes import criar_ambiente_compartilhado, entrar_ambiente_por_codigo, listar_turmas_para_ambiente
from cadastro_contexto import cadastrar_somente_contexto_escolar
from db import cadastrar_contexto_escolar, listar_grupos_usuario, obter_contexto_grupo, registrar_perfil_usuario, usuario_tem_acesso_grupo
from security import current_role

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY é obrigatória. Configure a variável de ambiente antes de iniciar o aplicativo.")
app.secret_key = SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=os.getenv("FLASK_SESSION_COOKIE_SECURE", "true").lower() == "true", SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=2 * 1024 * 1024)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fisica-web")
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[], storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"), strategy="fixed-window")


def _auth_client():
    url = os.getenv("SUPABASE_URL", "").strip(); key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key: raise RuntimeError("Supabase Auth não configurado no ambiente.")
    return create_client(url, key)


def _salvar_sessao_auth(r):
    s = getattr(r, "session", None); u = getattr(r, "user", None)
    if s:
        session["access_token"] = getattr(s, "access_token", None); session["refresh_token"] = getattr(s, "refresh_token", None)
    if u:
        session["user_id"] = str(getattr(u, "id", "") or ""); session["user_email"] = getattr(u, "email", "") or ""
    return u


def _csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32); session["csrf_token"] = token
    return token


def _grupo_id_requisicao():
    return (request.args.get("grupo_id") or request.form.get("grupo_id") or "").strip()


@app.context_processor
def inject_security_helpers(): return {"csrf_token": _csrf_token, "current_role": current_role}


@app.before_request
def security_guard():
    path = request.path; public = {"/acesso", "/api/acesso/login", "/api/acesso/cadastro", "/api/acesso/status", "/api/health/supabase"}
    if path.startswith("/static/") or path in public: return None
    if not session.get("user_id"):
        if path.startswith("/api/"): return jsonify({"erro": "Autenticação necessária.", "destino": "/acesso"}), 401
        return redirect("/acesso")
    if request.method == "POST":
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token"); expected = session.get("csrf_token")
        if not supplied or not expected or not secrets.compare_digest(str(supplied), str(expected)):
            logger.warning("CSRF rejeitado: path=%s user=%s", path, session.get("user_id")); return jsonify({"erro": "Solicitação inválida. Atualize a página e tente novamente."}), 400

    # Regra central de compartilhamento: qualquer dado identificado por grupo
    # só pode ser acessado por um membro ativo daquele grupo.
    grupo_id = _grupo_id_requisicao()
    if grupo_id and not usuario_tem_acesso_grupo(session.get("user_id", ""), grupo_id):
        logger.warning("Acesso a grupo negado: path=%s user=%s grupo=%s", path, session.get("user_id"), grupo_id)
        if path.startswith("/api/"):
            return jsonify({"erro": "Você não pertence a este grupo."}), 403
        return render_template("403.html"), 403

    # Alunos podem trabalhar no grupo e registrar medições, mas não podem
    # criar grupos por rotas legadas nem apagar o grupo inteiro ou limpar o histórico.
    if request.method == "POST" and (path == "/salvar-grupo" or path == "/excluir-grupo" or path.startswith("/limpar-")):
        if current_role() not in {"professor", "admin_instituicao", "admin_plataforma"}:
            return render_template("403.html"), 403


@app.after_request
def inject_accessibility_layers(response):
    if "text/html" not in response.headers.get("Content-Type", "").lower(): return response
    try:
        body = response.get_data(as_text=True)
        markers = ('<script src="/static/accessibility-voice.js" defer></script>', '<script src="/static/accessibility-science.js" defer></script>', '<script src="/static/experiment-illustrations.js" defer></script>', '<script src="/static/participant-persistence.js" defer></script>')
        for marker in markers:
            if marker not in body and "</body>" in body: body = body.replace("</body>", f"{marker}</body>", 1)
        response.set_data(body)
    except Exception: logger.exception("Falha ao injetar camadas de acessibilidade")
    return response


@app.route("/api/acesso/login", methods=["POST"])
@limiter.limit("5 per minute")
def api_acesso_login():
    d = request.get_json(silent=True) or {}; email = str(d.get("email") or "").strip().lower(); senha = str(d.get("senha") or "")
    if not email or not senha: return jsonify({"erro": "Informe e-mail e senha."}), 400
    try:
        u = _salvar_sessao_auth(_auth_client().auth.sign_in_with_password({"email": email, "password": senha}))
        if not u: return jsonify({"erro": "Não foi possível criar a sessão."}), 401
        session["csrf_token"] = secrets.token_urlsafe(32); return jsonify({"ok": True, "destino": "/meus-grupos"})
    except Exception:
        logger.exception("Falha de autenticação"); return jsonify({"erro": "E-mail ou senha inválidos."}), 401


@app.route("/api/acesso/cadastro", methods=["POST"])
def api_acesso_cadastro():
    d = request.get_json(silent=True) or {}; nome = str(d.get("nome") or "").strip(); email = str(d.get("email") or "").strip().lower(); senha = str(d.get("senha") or ""); papel = str(d.get("papel") or "professor").strip().lower()
    if papel not in {"professor", "estudante"}: papel = "professor"
    if not nome or not email or len(senha) < 8: return jsonify({"erro": "Informe nome, e-mail e uma senha com pelo menos 8 caracteres."}), 400
    try:
        resposta = _auth_client().auth.sign_up({"email": email, "password": senha, "options": {"data": {"nome": nome, "papel_solicitado": papel}}}); user = _salvar_sessao_auth(resposta)
        if user: registrar_perfil_usuario(str(user.id), nome, papel)
        if session.get("user_id"):
            session["csrf_token"] = secrets.token_urlsafe(32); return jsonify({"ok": True, "destino": "/meus-grupos"})
        return jsonify({"ok": True, "mensagem": "Cadastro criado. Confirme o e-mail se solicitado."})
    except Exception as exc:
        logger.exception("Falha ao criar cadastro")
        if any(x in str(exc).lower() for x in ("already", "registered", "exists")): return jsonify({"erro": "Este e-mail já possui cadastro."}), 409
        return jsonify({"erro": "Não foi possível criar o cadastro agora."}), 400


@app.route("/api/acesso/status")
def api_acesso_status(): return jsonify({"autenticado": bool(session.get("user_id")), "email": session.get("user_email", ""), "papel": current_role()})


@app.route("/api/acesso/logout", methods=["POST"])
def api_acesso_logout(): session.clear(); return jsonify({"ok": True, "destino": "/acesso"})


@app.route("/sair", methods=["POST"])
def sair(): session.clear(); return redirect("/acesso")


@app.errorhandler(403)
def erro_403(_exc): return render_template("403.html"), 403
@app.errorhandler(404)
def erro_404(_exc): return render_template("404.html"), 404
@app.errorhandler(429)
def erro_429(_exc): return render_template("429.html"), 429
@app.errorhandler(500)
def erro_500(exc): logger.exception("Erro interno não tratado", exc_info=exc); return render_template("500.html"), 500


@app.route("/meus-grupos")
def meus_grupos(): return render_template("meus_grupos.html", grupos=listar_grupos_usuario(session.get("user_id", "")), email=session.get("user_email", ""), papel=current_role())


@app.route("/api/grupo/<grupo_id>/participantes")
def api_grupo_participantes(grupo_id):
    try:
        contexto = obter_contexto_grupo(grupo_id.strip())
        if not contexto: return jsonify({"erro": "Grupo não encontrado.", "participantes": []}), 404
        participantes = contexto.get("participantes") or []
        return jsonify({"participantes": [{"codigo": p.get("codigo_participante", ""), "nome": p.get("nome_exibicao", "")} for p in participantes]})
    except PermissionError as exc: return jsonify({"erro": str(exc), "participantes": []}), 403
    except Exception:
        logger.exception("Falha ao carregar participantes do grupo"); return jsonify({"erro": "Não foi possível carregar os participantes.", "participantes": []}), 500


@app.route("/cadastro-escolar", methods=["GET", "POST"])
def cadastro_escolar():
    mensagem = ""; erro = ""; role = current_role()
    if role not in {"professor", "admin_instituicao", "admin_plataforma"}:
        return render_template("403.html"), 403
    if request.method == "POST":
        try:
            resultado = cadastrar_somente_contexto_escolar({
                "escola": request.form.get("escola", "").strip(),
                "rede": request.form.get("rede", "").strip(),
                "municipio": request.form.get("municipio", "").strip(),
                "estado": request.form.get("estado", "").strip(),
                "ano_letivo": request.form.get("ano_letivo", "").strip() or "2026",
                "serie": request.form.get("serie", "").strip(),
                "turma": request.form.get("turma", "").strip(),
                "turno": request.form.get("turno", "").strip(),
                "componente_curricular": request.form.get("componente_curricular", "Física").strip() or "Física",
                "professor_responsavel": session.get("user_email", ""),
            }, session.get("user_id", ""))
            turma = resultado.get("turma") or {}; escola = resultado.get("escola") or {}
            mensagem = f"Contexto escolar salvo. {escola.get('nome', 'Sua escola')} · {turma.get('serie_ano', '')} · Turma {turma.get('turma', '')}. Agora você pode criar um grupo experimental."
        except (LookupError, PermissionError, ValueError) as exc: erro = str(exc)
        except Exception:
            logger.exception("Falha ao cadastrar contexto escolar"); erro = "Não foi possível salvar o contexto escolar. Verifique os dados e tente novamente."
    return render_template("cadastro_escolar.html", mensagem=mensagem, erro=erro, email=session.get("user_email", ""))


@app.route("/ambiente", methods=["GET", "POST"])
def ambiente():
    uid = session.get("user_id", ""); role = current_role(); mensagem = ""; erro = ""; criado = None
    if request.method == "POST":
        try:
            acao = request.form.get("acao", "").strip().lower()
            if acao == "criar":
                if role not in {"professor", "admin_instituicao", "admin_plataforma"}: return render_template("403.html"), 403
                criado = criar_ambiente_compartilhado(user_id=uid, titulo=request.form.get("titulo", ""), experimento=request.form.get("experimento", ""), turma_id=request.form.get("turma_id", ""), professor_responsavel=session.get("user_email", ""))
                # O ambiente já foi criado e o experimento já está vinculado ao grupo.
                # A próxima etapa deve ser o próprio ambiente experimental, onde o
                # professor informa os participantes sem voltar à tela de criação.
                return redirect(f"/?grupo_id={criado['grupo']['id']}&experimento={request.form.get('experimento', '').strip().lower()}#contexto")
            elif acao == "entrar":
                resultado = entrar_ambiente_por_codigo(uid, request.form.get("codigo", "")); return redirect(f"/?grupo_id={resultado['grupo']['id']}#contexto")
            else: erro = "Escolha criar ou entrar em um ambiente."
        except (LookupError, PermissionError, ValueError) as exc: erro = str(exc)
        except Exception:
            logger.exception("Falha inesperada na operação de ambiente"); erro = "Não foi possível concluir a operação. Verifique os dados e tente novamente."
    return render_template("ambiente.html", turmas=listar_turmas_para_ambiente(uid), mensagem=mensagem, erro=erro, criado=criado, papel=role)


@app.route("/configuracao-experimental")
def configuracao_experimental(): return render_template("configuracao_experimental.html")

LABORATORIOS = {"movel":"laboratorio_movel.html", "sensores":"laboratorio_sensores.html", "elevador":"laboratorio_elevador.html", "pendulo":"laboratorio_pendulo.html", "plano-inclinado":"laboratorio_plano_inclinado.html", "som":"laboratorio_som.html", "mru":"laboratorio_mru.html", "mruv":"laboratorio_mruv.html", "queda-livre":"laboratorio_queda_livre.html", "lancamento":"laboratorio_lancamento.html", "newton":"laboratorio-newton.html", "energia":"laboratorio-energia.html", "atrito":"laboratorio-atrito.html", "circular":"laboratorio-circular.html"}

@app.route("/laboratorio/<nome>")
def laboratorio(nome):
    template = LABORATORIOS.get(nome)
    if not template: return render_template("404.html"), 404
    return render_template(template)

for _nome, _template in LABORATORIOS.items():
    _endpoint = f"legacy_laboratorio_{_nome.replace('-', '_')}"; _path = f"/laboratorio-{_nome}"; app.add_url_rule(_path, _endpoint, lambda template=_template: render_template(template))

if __name__ == "__main__": app.run(debug=False)
