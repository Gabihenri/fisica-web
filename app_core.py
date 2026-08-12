from flask import Flask, render_template, request, redirect, jsonify, send_file
import io
import json
import math
import os

from db import (
    cadastrar_contexto_escolar,
    limpar_medicoes,
    listar_medicoes,
    obter_contexto_grupo,
    registrar_medicao,
    salvar_resultado,
    verificar_conexao_supabase,
)
from report_engine import gerar_pdf_cientifico, _grafico_temp
from scientific_engine import GRAVIDADE_REFERENCIA, analisar_experimento


app = Flask(__name__)

dados_queda = []
dados_pendulo = []
dados_plano = []
CAMINHO_GRUPO = "grupo_Leandro.json"


def parse_numero(valor):
    return float(str(valor).strip().replace(",", "."))


def converter_medicoes_banco(chave, linhas):
    dados = []
    for linha in linhas:
        if chave == "queda":
            dados.append({
                "altura": float(linha["altura_m"]),
                "tempo": float(linha["tempo_s"]),
                "gravidade": float(linha["gravidade_m_s2"]),
            })
        elif chave == "pendulo":
            dados.append({
                "comprimento": float(linha["comprimento_m"]),
                "periodo": float(linha["periodo_s"]),
                "gravidade": float(linha["gravidade_m_s2"]),
            })
        elif chave == "plano":
            dados.append({
                "angulo": float(linha["angulo_graus"]),
                "distancia": float(linha["distancia_m"]),
                "tempo": float(linha["tempo_s"]),
                "aceleracao": float(linha["aceleracao_m_s2"]),
                "gravidade": float(linha["gravidade_m_s2"]),
            })
    return dados


def dados_persistidos(grupo_id, chave):
    if not grupo_id:
        return None
    try:
        return converter_medicoes_banco(chave, listar_medicoes(grupo_id, chave))
    except Exception:
        return None


def configuracao_experimento(chave, grupo_id=None):
    persistidos = dados_persistidos(grupo_id, chave)
    configuracoes = {
        "queda": {
            "dados": persistidos if persistidos is not None else dados_queda,
            "titulo": "Queda Livre",
            "teoria": (
                "A queda livre e um movimento uniformemente acelerado sob acao da gravidade. "
                "Desprezando a resistencia do ar e considerando velocidade inicial nula, "
                "a gravidade pode ser estimada por g = 2h/t^2."
            ),
        },
        "pendulo": {
            "dados": persistidos if persistidos is not None else dados_pendulo,
            "titulo": "Pendulo Simples",
            "teoria": (
                "Para pequenas oscilacoes, o periodo de um pendulo simples depende do comprimento "
                "e da aceleracao da gravidade. A estimativa e g = 4*pi^2*L/T^2."
            ),
        },
        "plano": {
            "dados": persistidos if persistidos is not None else dados_plano,
            "titulo": "Plano Inclinado",
            "teoria": (
                "Em um plano inclinado ideal, a componente da aceleracao paralela ao plano e "
                "a = g*sen(theta). A partir da distancia e do tempo estima-se a aceleracao e g."
            ),
        },
    }
    return configuracoes.get(chave)


def atualizar_resultado_persistido(grupo_id, chave, dados):
    if not grupo_id:
        return
    analise = analisar_experimento(chave, dados)
    try:
        salvar_resultado(grupo_id, chave, analise["estatisticas"], analise["interpretacao"])
    except Exception:
        pass


def relatorio_acessivel(chave, config):
    analise = analisar_experimento(chave, config["dados"])
    stats = analise["estatisticas"]
    modelo = analise["modelo"]

    medicoes = []
    for indice, item in enumerate(config["dados"], start=1):
        if chave == "queda":
            medicoes.append(
                f"Medicao {indice}: altura {item['altura']} metros, tempo {item['tempo']} segundos, "
                f"gravidade calculada {item['gravidade']:.4f} metros por segundo ao quadrado."
            )
        elif chave == "pendulo":
            medicoes.append(
                f"Medicao {indice}: comprimento {item['comprimento']} metros, periodo {item['periodo']} segundos, "
                f"gravidade calculada {item['gravidade']:.4f} metros por segundo ao quadrado."
            )
        else:
            medicoes.append(
                f"Medicao {indice}: angulo {item['angulo']} graus, distancia {item['distancia']} metros, "
                f"tempo {item['tempo']} segundos e gravidade calculada {item['gravidade']:.4f} metros por segundo ao quadrado."
            )

    if not medicoes:
        medicoes = ["Nenhuma medicao foi registrada ate o momento."]

    if stats["n"]:
        resumo = (
            f"Foram analisadas {stats['n']} medicoes. A media de g foi {stats['media']:.4f} metros por segundo ao quadrado, "
            f"com erro percentual de {stats['erro_percentual']:.2f} por cento. "
            f"A classificacao experimental foi {stats['qualidade']}."
        )
    else:
        resumo = "Ainda nao ha resultados experimentais suficientes para analise."

    descricao_grafico = modelo.get("descricao_modelo") or ""
    if modelo.get("regressao"):
        descricao_grafico += (
            f" O ajuste linear apresentou coeficiente de determinacao R ao quadrado igual a "
            f"{modelo['regressao']['r2']:.4f}."
        )
    if modelo.get("gravidade_modelo") is not None:
        descricao_grafico += f" A estimativa grafica de g foi {modelo['gravidade_modelo']:.4f} metros por segundo ao quadrado."

    parecer = (
        "Parecer pedagogico: compare o resultado com o modelo teorico, observe a dispersao das repeticoes "
        "e discuta fontes de incerteza como resolucao dos instrumentos, tempo de reacao e montagem experimental."
    )

    abertura = (
        f"Relatorio acessivel do experimento {config['titulo']}. "
        f"O valor de referencia adotado para g e {GRAVIDADE_REFERENCIA:.5f} metros por segundo ao quadrado."
    )
    texto = " ".join([abertura] + medicoes + [resumo, descricao_grafico, analise["interpretacao"], parecer])
    return {
        "experimento": chave,
        "titulo": config["titulo"],
        "estatisticas": stats,
        "modelo": modelo,
        "secoes": {
            "abertura": abertura,
            "medicoes": medicoes,
            "resultado": resumo,
            "audiodescricao_grafico": descricao_grafico,
            "interpretacao": analise["interpretacao"],
            "parecer_pedagogico": parecer,
        },
        "texto_completo": texto,
    }


@app.route("/")
def index():
    grupo_id = request.args.get("grupo_id", "").strip()
    contexto = None
    mensagem_banco = ""
    if grupo_id:
        try:
            contexto = obter_contexto_grupo(grupo_id)
        except Exception:
            mensagem_banco = "Nao foi possivel carregar o contexto persistido do banco."

    q = dados_persistidos(grupo_id, "queda") if grupo_id else None
    p = dados_persistidos(grupo_id, "pendulo") if grupo_id else None
    pl = dados_persistidos(grupo_id, "plano") if grupo_id else None
    dados_q = q if q is not None else dados_queda
    dados_p = p if p is not None else dados_pendulo
    dados_pl = pl if pl is not None else dados_plano

    return render_template(
        "index.html",
        grupo_id=grupo_id,
        contexto=contexto,
        mensagem_banco=mensagem_banco,
        dados_queda=dados_q,
        dados_pendulo=dados_p,
        dados_plano=dados_pl,
        estatisticas_queda=analisar_experimento("queda", dados_q)["estatisticas"],
        estatisticas_pendulo=analisar_experimento("pendulo", dados_p)["estatisticas"],
        estatisticas_plano=analisar_experimento("plano", dados_pl)["estatisticas"],
    )


@app.route("/api/health/supabase")
def api_health_supabase():
    resultado = verificar_conexao_supabase()
    return jsonify(resultado), 200 if resultado.get("ok") else 503


@app.route("/salvar-grupo", methods=["POST"])
def salvar_grupo():
    nomes = [request.form.get(f"nome{i}", "").strip() for i in range(1, 6)]
    grupo_local = {"nomes": nomes, "turma": request.form.get("turma", ""), "serie": request.form.get("serie", "")}
    try:
        with open(CAMINHO_GRUPO, "w", encoding="utf-8") as arquivo:
            json.dump(grupo_local, arquivo, ensure_ascii=False, indent=2)
    except OSError:
        pass

    payload = {
        "nomes": nomes,
        "escola": request.form.get("escola", ""),
        "rede": request.form.get("rede", ""),
        "municipio": request.form.get("municipio", ""),
        "estado": request.form.get("estado", ""),
        "ano_letivo": request.form.get("ano_letivo", ""),
        "serie": request.form.get("serie", ""),
        "turma": request.form.get("turma", ""),
        "turno": request.form.get("turno", ""),
        "componente_curricular": request.form.get("componente_curricular", "Fisica"),
        "professor_responsavel": request.form.get("professor_responsavel", ""),
        "codigo_grupo": request.form.get("codigo_grupo", "Grupo 1"),
    }
    try:
        contexto = cadastrar_contexto_escolar(payload)
        return redirect(f"/?grupo_id={contexto['grupo']['id']}")
    except Exception as exc:
        return f"Nao foi possivel salvar o contexto escolar no banco: {exc}", 500


@app.route("/queda-livre", methods=["POST"])
def queda_livre():
    try:
        altura = parse_numero(request.form["altura"])
        tempo = parse_numero(request.form["tempo"])
    except ValueError:
        return "Informe valores numericos validos para altura e tempo.", 400
    if altura <= 0 or tempo <= 0:
        return "Altura e tempo devem ser maiores que zero.", 400

    g = 2 * altura / (tempo ** 2)
    item = {"altura": altura, "tempo": tempo, "gravidade": round(g, 5)}
    grupo_id = request.form.get("grupo_id", "").strip()
    if grupo_id:
        registrar_medicao(grupo_id, "queda", {"altura_m": altura, "tempo_s": tempo, "gravidade_m_s2": round(g, 5)}, "manual")
        dados = dados_persistidos(grupo_id, "queda") or [item]
        atualizar_resultado_persistido(grupo_id, "queda", dados)
        return redirect(f"/?grupo_id={grupo_id}&experimento=queda#experimentos")
    dados_queda.append(item)
    return redirect("/?experimento=queda#experimentos")


@app.route("/pendulo", methods=["POST"])
def pendulo():
    try:
        comprimento = parse_numero(request.form["comprimento"])
        periodo = parse_numero(request.form["periodo"])
    except ValueError:
        return "Informe valores numericos validos para comprimento e periodo.", 400
    if comprimento <= 0 or periodo <= 0:
        return "Comprimento e periodo devem ser maiores que zero.", 400

    g = (4 * math.pi ** 2 * comprimento) / (periodo ** 2)
    item = {"comprimento": comprimento, "periodo": periodo, "gravidade": round(g, 5)}
    grupo_id = request.form.get("grupo_id", "").strip()
    if grupo_id:
        registrar_medicao(grupo_id, "pendulo", {"comprimento_m": comprimento, "periodo_s": periodo, "gravidade_m_s2": round(g, 5)}, "manual")
        dados = dados_persistidos(grupo_id, "pendulo") or [item]
        atualizar_resultado_persistido(grupo_id, "pendulo", dados)
        return redirect(f"/?grupo_id={grupo_id}&experimento=pendulo#experimentos")
    dados_pendulo.append(item)
    return redirect("/?experimento=pendulo#experimentos")


@app.route("/plano", methods=["POST"])
def plano():
    try:
        angulo = parse_numero(request.form["angulo"])
        distancia = parse_numero(request.form["distancia"])
        tempo = parse_numero(request.form["tempo"])
    except ValueError:
        return "Informe valores numericos validos para angulo, distancia e tempo.", 400
    if angulo <= 0 or angulo >= 90:
        return "O angulo deve estar entre 0 e 90 graus.", 400
    if distancia <= 0 or tempo <= 0:
        return "Distancia e tempo devem ser maiores que zero.", 400

    aceleracao = 2 * distancia / (tempo ** 2)
    g = aceleracao / math.sin(math.radians(angulo))
    item = {
        "angulo": angulo,
        "distancia": distancia,
        "tempo": tempo,
        "aceleracao": round(aceleracao, 5),
        "gravidade": round(g, 5),
    }
    grupo_id = request.form.get("grupo_id", "").strip()
    if grupo_id:
        registrar_medicao(grupo_id, "plano", {
            "angulo_graus": angulo,
            "distancia_m": distancia,
            "tempo_s": tempo,
            "aceleracao_m_s2": round(aceleracao, 5),
            "gravidade_m_s2": round(g, 5),
        }, "manual")
        dados = dados_persistidos(grupo_id, "plano") or [item]
        atualizar_resultado_persistido(grupo_id, "plano", dados)
        return redirect(f"/?grupo_id={grupo_id}&experimento=plano#experimentos")
    dados_plano.append(item)
    return redirect("/?experimento=plano#experimentos")


@app.route("/limpar-<experimento>", methods=["POST"])
def limpar_experimento(experimento):
    if experimento not in ("queda", "pendulo", "plano"):
        return jsonify({"erro": "Experimento invalido"}), 404
    grupo_id = request.form.get("grupo_id", "").strip()
    if grupo_id:
        limpar_medicoes(grupo_id, experimento)
        return redirect(f"/?grupo_id={grupo_id}&experimento={experimento}#experimentos")
    if experimento == "queda":
        dados_queda.clear()
    elif experimento == "pendulo":
        dados_pendulo.clear()
    else:
        dados_plano.clear()
    return redirect(f"/?experimento={experimento}#experimentos")


@app.route("/api/analise/<experimento>")
def api_analise(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    config = configuracao_experimento(experimento, grupo_id)
    if not config:
        return jsonify({"erro": "Experimento invalido"}), 404
    return jsonify(analisar_experimento(experimento, config["dados"]))


@app.route("/api/estatisticas/<experimento>")
def api_estatisticas(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    config = configuracao_experimento(experimento, grupo_id)
    if not config:
        return jsonify({"erro": "Experimento invalido"}), 404
    analise = analisar_experimento(experimento, config["dados"])
    return jsonify({"experimento": experimento, "estatisticas": analise["estatisticas"], "interpretacao": analise["interpretacao"]})


@app.route("/api/relatorio-acessivel/<experimento>")
def api_relatorio_acessivel(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    config = configuracao_experimento(experimento, grupo_id)
    if not config:
        return jsonify({"erro": "Experimento invalido"}), 404
    return jsonify(relatorio_acessivel(experimento, config))


@app.route("/grafico/<experimento>")
def grafico_experimento(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    config = configuracao_experimento(experimento, grupo_id)
    if not config:
        return "Experimento invalido", 404
    caminho = _grafico_temp(analisar_experimento(experimento, config["dados"]))
    if not caminho or not os.path.exists(caminho):
        return "Ainda nao ha dados suficientes para gerar o grafico.", 404
    return send_file(caminho, mimetype="image/png", max_age=0)


@app.route("/relatorio/<experimento>")
def gerar_pdf(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    config = configuracao_experimento(experimento, grupo_id)
    if not config:
        return "Experimento nao identificado.", 404
    contexto = None
    if grupo_id:
        try:
            contexto = obter_contexto_grupo(grupo_id)
        except Exception:
            contexto = None
    buffer = gerar_pdf_cientifico(experimento, config["titulo"], config["teoria"], config["dados"], contexto)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"fisica_web_relatorio_{experimento}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
