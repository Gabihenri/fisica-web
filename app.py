import os

from flask import jsonify, redirect, render_template, request, session
from supabase import create_client

from app_core import app


app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.getenv("SECRET_KEY") or "fisica-web-dev-change-me"


def _auth_client():
    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("Supabase Auth não configurado no ambiente.")
    return create_client(url, key)


def _salvar_sessao_auth(auth_response):
    auth_session = getattr(auth_response, "session", None)
    user = getattr(auth_response, "user", None)
    if auth_session:
        session["access_token"] = getattr(auth_session, "access_token", None)
        session["refresh_token"] = getattr(auth_session, "refresh_token", None)
    if user:
        session["user_id"] = str(getattr(user, "id", "") or "")
        session["user_email"] = getattr(user, "email", "") or ""


@app.route("/acesso")
def acesso():
    return render_template("acesso.html")


@app.route("/api/acesso/login", methods=["POST"])
def api_acesso_login():
    dados = request.get_json(silent=True) or {}
    email = str(dados.get("email") or "").strip().lower()
    senha = str(dados.get("senha") or "")
    if not email or not senha:
        return jsonify({"erro": "Informe e-mail e senha."}), 400
    try:
        resposta = _auth_client().auth.sign_in_with_password({"email": email, "password": senha})
        _salvar_sessao_auth(resposta)
        return jsonify({"ok": True, "destino": "/"})
    except Exception:
        return jsonify({"erro": "E-mail ou senha inválidos, ou acesso ainda não confirmado."}), 401


@app.route("/api/acesso/cadastro", methods=["POST"])
def api_acesso_cadastro():
    dados = request.get_json(silent=True) or {}
    nome = str(dados.get("nome") or "").strip()
    email = str(dados.get("email") or "").strip().lower()
    senha = str(dados.get("senha") or "")
    papel = str(dados.get("papel") or "professor").strip().lower()
    if papel not in {"professor", "estudante"}:
        papel = "professor"
    if not nome or not email or len(senha) < 8:
        return jsonify({"erro": "Informe nome, e-mail e uma senha com pelo menos 8 caracteres."}), 400
    try:
        resposta = _auth_client().auth.sign_up({
            "email": email,
            "password": senha,
            "options": {"data": {"nome": nome, "papel_solicitado": papel}},
        })
        _salvar_sessao_auth(resposta)
        return jsonify({
            "ok": True,
            "mensagem": "Cadastro criado. Se a confirmação por e-mail estiver habilitada, confirme o endereço antes de entrar. O vínculo com instituição, turma e grupo será liberado separadamente.",
        })
    except Exception as exc:
        mensagem = str(exc).lower()
        if "already" in mensagem or "registered" in mensagem or "exists" in mensagem:
            return jsonify({"erro": "Este e-mail já possui cadastro."}), 409
        return jsonify({"erro": "Não foi possível criar o cadastro agora."}), 400


@app.route("/api/acesso/google")
def api_acesso_google():
    try:
        origem = request.url_root.rstrip("/")
        destino = f"{origem}/acesso"
        resposta = _auth_client().auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": destino},
        })
        url = getattr(resposta, "url", None)
        if not url and isinstance(resposta, dict):
            url = resposta.get("url")
        if not url:
            return jsonify({"erro": "O Google OAuth ainda não está habilitado no Supabase Auth."}), 503
        return redirect(url)
    except Exception as exc:
        mensagem = str(exc).lower()
        if "provider" in mensagem and ("enabled" in mensagem or "unsupported" in mensagem):
            return jsonify({"erro": "O provedor Google ainda não está habilitado no Supabase Auth."}), 503
        return jsonify({"erro": "Não foi possível iniciar o acesso pelo Google."}), 503


@app.route("/api/acesso/logout", methods=["POST"])
def api_acesso_logout():
    try:
        _auth_client().auth.sign_out()
    except Exception:
        pass
    session.clear()
    return jsonify({"ok": True, "destino": "/acesso"})


@app.route("/laboratorio-movel")
def laboratorio_movel():
    return render_template("laboratorio_movel.html")


@app.route("/laboratorio-sensores")
def laboratorio_sensores():
    return render_template("laboratorio_sensores.html")


@app.route("/laboratorio-elevador")
def laboratorio_elevador():
    return render_template("laboratorio_elevador.html")


@app.route("/laboratorio-pendulo")
def laboratorio_pendulo():
    return app.send_static_file("laboratorio-pendulo.html")


@app.route("/laboratorio-plano-inclinado")
def laboratorio_plano_inclinado():
    return render_template("laboratorio_plano_inclinado.html")


@app.route("/laboratorio-som")
def laboratorio_som():
    return render_template("laboratorio_som.html")


if __name__ == "__main__":
    app.run(debug=True)
