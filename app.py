import logging
import os

from flask import jsonify, redirect, render_template, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from supabase import create_client

from app_core import app
from db import listar_grupos_usuario, registrar_perfil_usuario
from ambientes import criar_ambiente_compartilhado, entrar_ambiente_por_codigo, listar_turmas_para_ambiente

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise RuntimeError("FLASK_SECRET_KEY é obrigatória. Configure a variável de ambiente antes de iniciar o aplicativo.")

app.secret_key = SECRET_KEY

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("fisica-web")

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    strategy="fixed-window",
)

def _auth_client():
    url=os.getenv("SUPABASE_URL","").strip(); key=os.getenv("SUPABASE_KEY","").strip()
    if not url or not key: raise RuntimeError("Supabase Auth não configurado no ambiente.")
    return create_client(url,key)

def _salvar_sessao_auth(r):
    s=getattr(r,"session",None); u=getattr(r,"user",None)
    if s: session["access_token"]=getattr(s,"access_token",None); session["refresh_token"]=getattr(s,"refresh_token",None)
    if u: session["user_id"]=str(getattr(u,"id","") or ""); session["user_email"]=getattr(u,"email","") or ""
    return u

@app.before_request
def exigir_login():
    p=request.path
    if p.startswith("/static/") or p in {"/acesso","/api/acesso/login","/api/acesso/cadastro","/api/acesso/status","/api/health/supabase"}: return None
    if not session.get("user_id"):
        if p.startswith("/api/"): return jsonify({"erro":"Autenticação necessária.","destino":"/acesso"}),401
        return redirect("/acesso")

@app.errorhandler(500)
def erro_500(exc):
    logger.exception("Erro interno não tratado", exc_info=exc)
    return render_template("500.html"), 500

@app.route("/api/acesso/login",methods=["POST"])
@limiter.limit("5 per minute")
def api_acesso_login():
    d=request.get_json(silent=True) or {}; email=str(d.get("email") or "").strip().lower(); senha=str(d.get("senha") or "")
    if not email or not senha:return jsonify({"erro":"Informe e-mail e senha."}),400
    try:
        u=_salvar_sessao_auth(_auth_client().auth.sign_in_with_password({"email":email,"password":senha}))
        if not u:return jsonify({"erro":"Não foi possível criar a sessão."}),401
        return jsonify({"ok":True,"destino":"/meus-grupos"})
    except Exception:
        logger.warning("Falha de autenticação para tentativa de login", extra={"ip":get_remote_address()})
        return jsonify({"erro":"E-mail ou senha inválidos."}),401

@app.route("/api/acesso/status")
def api_acesso_status():return jsonify({"autenticado":bool(session.get("user_id")),"email":session.get("user_email","")})
@app.route("/api/acesso/logout",methods=["POST"])
def api_acesso_logout():session.clear();return jsonify({"ok":True,"destino":"/acesso"})
@app.route("/sair",methods=["POST"])
def sair():session.clear();return redirect("/acesso")
@app.route("/meus-grupos")
def meus_grupos():return render_template("meus_grupos.html",grupos=listar_grupos_usuario(session.get("user_id","")),email=session.get("user_email",""))
@app.route("/ambiente",methods=["GET","POST"])
def ambiente():
    uid=session.get("user_id",""); mensagem=""; erro=""; criado=None
    if request.method=="POST":
        try:
            acao=request.form.get("acao","").strip().lower()
            if acao=="criar":
                criado=criar_ambiente_compartilhado(user_id=uid,titulo=request.form.get("titulo",""),experimento=request.form.get("experimento",""),turma_id=request.form.get("turma_id",""),professor_responsavel=session.get("user_email","")); mensagem=f"Ambiente criado. Código: {criado['codigo']}"
            elif acao=="entrar":
                r=entrar_ambiente_por_codigo(uid,request.form.get("codigo","")); return redirect(f"/?grupo_id={r['grupo']['id']}#contexto")
            else: erro="Escolha criar ou entrar em um ambiente."
        except (LookupError,PermissionError,ValueError) as e:
            logger.info("Operação de ambiente rejeitada: %s", e)
            erro=str(e)
        except Exception:
            logger.exception("Falha inesperada na operação de ambiente")
            erro="Não foi possível concluir a operação. Verifique os dados e tente novamente."
    return render_template("ambiente.html",turmas=listar_turmas_para_ambiente(uid),mensagem=mensagem,erro=erro,criado=criado)
@app.route("/configuracao-experimental")
def configuracao_experimental(): return render_template("configuracao_experimental.html")
@app.route("/laboratorio-movel")
def laboratorio_movel():return render_template("laboratorio_movel.html")
@app.route("/laboratorio-sensores")
def laboratorio_sensores():return render_template("laboratorio_sensores.html")
@app.route("/laboratorio-elevador")
def laboratorio_elevador():return render_template("laboratorio_elevador.html")
@app.route("/laboratorio-pendulo")
def laboratorio_pendulo():return app.send_static_file("laboratorio-pendulo.html")
@app.route("/laboratorio-plano-inclinado")
def laboratorio_plano_inclinado():return render_template("laboratorio_plano_inclinado.html")
@app.route("/laboratorio-som")
def laboratorio_som():return render_template("laboratorio_som.html")
@app.route("/laboratorio-mru")
def laboratorio_mru():return render_template("laboratorio_mru.html")
@app.route("/laboratorio-mruv")
def laboratorio_mruv():return render_template("laboratorio_mruv.html")
@app.route("/laboratorio-queda-livre")
def laboratorio_queda_livre():return render_template("laboratorio_queda_livre.html")
@app.route("/laboratorio-lancamento")
def laboratorio_lancamento():return render_template("laboratorio_lancamento.html")
@app.route("/laboratorio-newton")
def laboratorio_newton():return render_template("laboratorio-newton.html")
@app.route("/laboratorio-energia")
def laboratorio_energia():return render_template("laboratorio-energia.html")
@app.route("/laboratorio-atrito")
def laboratorio_atrito():return render_template("laboratorio-atrito.html")
@app.route("/laboratorio-circular")
def laboratorio_circular():return render_template("laboratorio-circular.html")
if __name__=="__main__":app.run(debug=True)