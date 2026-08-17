import os

from flask import jsonify, redirect, render_template, request, session
from supabase import create_client

from app_core import app
from db import listar_grupos_usuario, registrar_perfil_usuario
from ambientes import criar_ambiente_compartilhado, entrar_ambiente_por_codigo, listar_turmas_para_ambiente

app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or os.urandom(32)

def _auth_client():
    url = os.getenv("SUPABASE_URL", "").strip(); key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key: raise RuntimeError("Supabase Auth não configurado no ambiente.")
    return create_client(url, key)

@app.after_request
def aplicar_home_clean_css(response):
    if request.path == "/" and response.content_type and response.content_type.startswith("text/html"):
        conteudo=response.get_data(); marcador=b"</head>"
        if b"home-clean.css" not in conteudo and marcador in conteudo:
            conteudo=conteudo.replace(marcador,b'<link rel="stylesheet" href="/static/home-clean.css?v=1">\n</head>',1); response.set_data(conteudo)
    return response

def _salvar_sessao_auth(auth_response):
    auth_session=getattr(auth_response,"session",None); user=getattr(auth_response,"user",None)
    if auth_session:
        session["access_token"]=getattr(auth_session,"access_token",None); session["refresh_token"]=getattr(auth_session,"refresh_token",None)
    if user:
        session["user_id"]=str(getattr(user,"id","") or ""); session["user_email"]=getattr(user,"email","") or ""
    return user

@app.before_request
def exigir_login():
    caminho=request.path
    if caminho.startswith("/static/"): return None
    publicos={"/acesso","/api/acesso/login","/api/acesso/cadastro","/api/acesso/status","/api/health/supabase"}
    if caminho in publicos: return None
    if not session.get("user_id"):
        if caminho.startswith("/api/"): return jsonify({"erro":"Autenticação necessária.","destino":"/acesso"}),401
        return redirect("/acesso")
    return None

@app.route("/api/acesso/login",methods=["POST"])
def api_acesso_login():
    dados=request.get_json(silent=True) or {}; email=str(dados.get("email") or "").strip().lower(); senha=str(dados.get("senha") or "")
    if not email or not senha: return jsonify({"erro":"Informe e-mail e senha."}),400
    try:
        resposta=_auth_client().auth.sign_in_with_password({"email":email,"password":senha}); user=_salvar_sessao_auth(resposta)
        if not user or not session.get("user_id"): return jsonify({"erro":"Não foi possível criar a sessão."}),401
        return jsonify({"ok":True,"destino":"/meus-grupos"})
    except Exception: return jsonify({"erro":"E-mail ou senha inválidos."}),401

@app.route("/api/acesso/cadastro",methods=["POST"])
def api_acesso_cadastro():
    dados=request.get_json(silent=True) or {}; nome=str(dados.get("nome") or "").strip(); email=str(dados.get("email") or "").strip().lower(); senha=str(dados.get("senha") or ""); papel=str(dados.get("papel") or "professor").strip().lower()
    if papel not in {"professor","estudante"}: papel="professor"
    if not nome or not email or len(senha)<8: return jsonify({"erro":"Informe nome, e-mail e uma senha com pelo menos 8 caracteres."}),400
    cliente=_auth_client()
    try:
        criado=cliente.auth.admin.create_user({"email":email,"password":senha,"email_confirm":True,"user_metadata":{"nome":nome,"papel_solicitado":papel}}); user=getattr(criado,"user",None)
        if user: registrar_perfil_usuario(str(user.id),nome,papel)
        resposta=_auth_client().auth.sign_in_with_password({"email":email,"password":senha}); _salvar_sessao_auth(resposta)
        return jsonify({"ok":True,"destino":"/meus-grupos","mensagem":"Cadastro criado. Você já pode usar o Física Web."})
    except Exception as admin_exc:
        if any(x in str(admin_exc).lower() for x in ("already","registered","exists")): return jsonify({"erro":"Este e-mail já possui cadastro."}),409
        try:
            resposta=_auth_client().auth.sign_up({"email":email,"password":senha,"options":{"data":{"nome":nome,"papel_solicitado":papel}}}); user=_salvar_sessao_auth(resposta)
            if user: registrar_perfil_usuario(str(user.id),nome,papel)
            if session.get("user_id"): return jsonify({"ok":True,"destino":"/meus-grupos","mensagem":"Cadastro criado. Você já pode usar o Física Web."})
            return jsonify({"ok":True,"mensagem":"Cadastro criado. Confirme o e-mail apenas se o Supabase solicitar e depois entre normalmente."})
        except Exception as exc:
            if any(x in str(exc).lower() for x in ("already","registered","exists")): return jsonify({"erro":"Este e-mail já possui cadastro."}),409
            return jsonify({"erro":"Não foi possível criar o cadastro agora."}),400

@app.route("/api/acesso/status")
def api_acesso_status(): return jsonify({"autenticado":bool(session.get("user_id")),"email":session.get("user_email",""),"rota_acesso":"/acesso"})
@app.route("/api/acesso/logout",methods=["POST"])
def api_acesso_logout(): session.clear(); return jsonify({"ok":True,"destino":"/acesso"})
@app.route("/sair",methods=["POST"])
def sair(): session.clear(); return redirect("/acesso")

@app.route("/meus-grupos")
def meus_grupos(): return render_template("meus_grupos.html",grupos=listar_grupos_usuario(session.get("user_id","")),email=session.get("user_email",""))

@app.route("/ambiente",methods=["GET","POST"])
def ambiente():
    user_id=session.get("user_id",""); mensagem=""; erro=""; criado=None
    if request.method=="POST":
        try:
            acao=request.form.get("acao","").strip().lower()
            if acao=="criar":
                criado=criar_ambiente_compartilhado(user_id=user_id,titulo=request.form.get("titulo",""),experimento=request.form.get("experimento",""),turma_id=request.form.get("turma_id",""),professor_responsavel=session.get("user_email","")); mensagem=f"Ambiente criado. Código: {criado['codigo']}"
            elif acao=="entrar":
                resultado=entrar_ambiente_por_codigo(user_id,request.form.get("codigo","")); return redirect(f"/?grupo_id={resultado['grupo']['id']}#contexto")
            else: erro="Escolha criar ou entrar em um ambiente."
        except LookupError as exc: erro=str(exc)
        except (PermissionError,ValueError) as exc: erro=str(exc)
        except Exception: erro="Não foi possível concluir a operação. Verifique os dados e tente novamente."
    return render_template("ambiente.html",turmas=listar_turmas_para_ambiente(user_id),mensagem=mensagem,erro=erro,criado=criado)

@app.route("/laboratorio-movel")
def laboratorio_movel(): return render_template("laboratorio_movel.html")
@app.route("/laboratorio-sensores")
def laboratorio_sensores(): return render_template("laboratorio_sensores.html")
@app.route("/laboratorio-elevador")
def laboratorio_elevador(): return render_template("laboratorio_elevador.html")
@app.route("/laboratorio-pendulo")
def laboratorio_pendulo(): return app.send_static_file("laboratorio-pendulo.html")
@app.route("/laboratorio-plano-inclinado")
def laboratorio_plano_inclinado(): return render_template("laboratorio_plano_inclinado.html")
@app.route("/laboratorio-som")
def laboratorio_som(): return render_template("laboratorio_som.html")
@app.route("/laboratorio-mru")
def laboratorio_mru(): return render_template("laboratorio_mru.html")
@app.route("/laboratorio-mruv")
def laboratorio_mruv(): return render_template("laboratorio_mruv.html")
@app.route("/laboratorio-queda-livre")
def laboratorio_queda_livre(): return render_template("laboratorio_queda_livre.html")
@app.route("/laboratorio-lancamento")
def laboratorio_lancamento(): return render_template("laboratorio_lancamento.html")
@app.route("/laboratorio-newton")
def laboratorio_newton(): return render_template("laboratorio-newton.html")
@app.route("/laboratorio-energia")
def laboratorio_energia(): return render_template("laboratorio-energia.html")

if __name__=="__main__": app.run(debug=True)