from flask import Flask, render_template, request, redirect, jsonify, send_file
import io
import json
import math
import os
import statistics
import tempfile

from fpdf import FPDF
import matplotlib.pyplot as plt

from db import (
    cadastrar_contexto_escolar,
    limpar_medicoes,
    listar_medicoes,
    obter_contexto_grupo,
    registrar_medicao,
    salvar_resultado,
    verificar_conexao_supabase,
)


app = Flask(__name__)

dados_queda = []
dados_pendulo = []
dados_plano = []

CAMINHO_GRUPO = "grupo_Leandro.json"
GRAVIDADE_REFERENCIA = 9.80665


def parse_numero(valor):
    return float(str(valor).strip().replace(",", "."))


def classificar_qualidade(erro_percentual):
    if erro_percentual is None:
        return "Dados insuficientes"
    if erro_percentual <= 5:
        return "Excelente"
    if erro_percentual <= 10:
        return "Boa"
    if erro_percentual <= 20:
        return "Regular"
    return "Requer revisão experimental"


def interpretar_resultado(estatisticas):
    if estatisticas["n"] == 0:
        return "Ainda não há medidas suficientes para interpretar o experimento."

    media = estatisticas["media"]
    erro = estatisticas["erro_percentual"]
    desvio = estatisticas["desvio_padrao"]
    qualidade = estatisticas["qualidade"]

    if erro <= 5:
        proximidade = "muito próximo do valor de referência"
    elif erro <= 10:
        proximidade = "próximo do valor de referência"
    elif erro <= 20:
        proximidade = "moderadamente distante do valor de referência"
    else:
        proximidade = "distante do valor de referência"

    if estatisticas["n"] == 1:
        dispersao = "Há apenas uma medida; por isso ainda não é possível avaliar a dispersão entre repetições."
    elif desvio <= 0.2:
        dispersao = "As medidas apresentam baixa dispersão entre si."
    elif desvio <= 0.8:
        dispersao = "As medidas apresentam dispersão moderada."
    else:
        dispersao = "As medidas apresentam dispersão elevada e recomendam revisão do procedimento experimental."

    return (
        f"A média experimental obtida foi {media:.4f} metros por segundo ao quadrado, {proximidade}. "
        f"O erro percentual foi {erro:.2f} por cento, resultando em classificação {qualidade}. "
        f"{dispersao}"
    )


def calcular_estatisticas(dados):
    valores_g = [float(item["gravidade"]) for item in dados if "gravidade" in item]

    if not valores_g:
        return {
            "n": 0,
            "media": None,
            "desvio_padrao": None,
            "erro_percentual": None,
            "qualidade": "Dados insuficientes",
            "gravidade_referencia": GRAVIDADE_REFERENCIA,
            "minimo": None,
            "maximo": None,
        }

    media = statistics.mean(valores_g)
    desvio_padrao = statistics.stdev(valores_g) if len(valores_g) > 1 else 0.0
    erro_percentual = abs(media - GRAVIDADE_REFERENCIA) / GRAVIDADE_REFERENCIA * 100

    return {
        "n": len(valores_g),
        "media": round(media, 4),
        "desvio_padrao": round(desvio_padrao, 4),
        "erro_percentual": round(erro_percentual, 2),
        "qualidade": classificar_qualidade(erro_percentual),
        "gravidade_referencia": GRAVIDADE_REFERENCIA,
        "minimo": round(min(valores_g), 4),
        "maximo": round(max(valores_g), 4),
    }


def converter_medicoes_banco(chave_experimento, linhas):
    dados = []
    for linha in linhas:
        if chave_experimento == "queda":
            dados.append({
                "altura": float(linha["altura_m"]),
                "tempo": float(linha["tempo_s"]),
                "gravidade": float(linha["gravidade_m_s2"]),
            })
        elif chave_experimento == "pendulo":
            dados.append({
                "comprimento": float(linha["comprimento_m"]),
                "periodo": float(linha["periodo_s"]),
                "gravidade": float(linha["gravidade_m_s2"]),
            })
        elif chave_experimento == "plano":
            dados.append({
                "angulo": float(linha["angulo_graus"]),
                "distancia": float(linha["distancia_m"]),
                "tempo": float(linha["tempo_s"]),
                "aceleracao": float(linha["aceleracao_m_s2"]),
                "gravidade": float(linha["gravidade_m_s2"]),
            })
    return dados


def dados_persistidos(grupo_id, chave_experimento):
    if not grupo_id:
        return None
    try:
        return converter_medicoes_banco(chave_experimento, listar_medicoes(grupo_id, chave_experimento))
    except Exception:
        return None


def obter_configuracao_experimento(experimento, grupo_id=None):
    persistidos = dados_persistidos(grupo_id, experimento)
    configuracoes = {
        "queda": {
            "dados": persistidos if persistidos is not None else dados_queda,
            "titulo": "Queda Livre",
            "teoria": (
                "A queda livre é um movimento uniformemente acelerado sob ação da gravidade. "
                "Desprezando a resistência do ar e considerando velocidade inicial nula, "
                "a aceleração gravitacional pode ser estimada pela relação g = 2h/t^2."
            ),
        },
        "pendulo": {
            "dados": persistidos if persistidos is not None else dados_pendulo,
            "titulo": "Pêndulo Simples",
            "teoria": (
                "Para pequenas oscilações, o período de um pêndulo simples depende do "
                "comprimento do fio e da aceleração da gravidade. A estimativa experimental "
                "é obtida pela relação g = 4*pi^2*L/T^2."
            ),
        },
        "plano": {
            "dados": persistidos if persistidos is not None else dados_plano,
            "titulo": "Plano Inclinado",
            "teoria": (
                "Em um plano inclinado ideal, a componente da aceleração paralela ao plano "
                "é a = g*sen(angulo). A partir da distância percorrida e do tempo, estima-se "
                "a aceleração e, consequentemente, o valor experimental de g."
            ),
        },
    }
    return configuracoes.get(experimento)


def descrever_medicoes_para_audio(experimento, dados):
    if not dados:
        return ["Nenhuma medição foi registrada até o momento."]

    descricoes = []
    for indice, item in enumerate(dados, start=1):
        if experimento == "queda":
            texto = (
                f"Medição {indice}: altura de {item['altura']} metros, "
                f"tempo de {item['tempo']} segundos e gravidade calculada de "
                f"{item['gravidade']:.4f} metros por segundo ao quadrado."
            )
        elif experimento == "pendulo":
            texto = (
                f"Medição {indice}: comprimento do pêndulo de {item['comprimento']} metros, "
                f"período de {item['periodo']} segundos e gravidade calculada de "
                f"{item['gravidade']:.4f} metros por segundo ao quadrado."
            )
        else:
            texto = (
                f"Medição {indice}: ângulo de {item['angulo']} graus, distância de "
                f"{item['distancia']} metros, tempo de {item['tempo']} segundos, aceleração de "
                f"{item['aceleracao']:.4f} metros por segundo ao quadrado e gravidade calculada de "
                f"{item['gravidade']:.4f} metros por segundo ao quadrado."
            )
        descricoes.append(texto)
    return descricoes


def audiodescrever_grafico(dados, estatisticas):
    if not dados or estatisticas["n"] == 0:
        return "Não há gráfico disponível porque ainda não existem medidas registradas."

    valores = [float(item["gravidade"]) for item in dados]
    indice_min = valores.index(min(valores)) + 1
    indice_max = valores.index(max(valores)) + 1

    if estatisticas["media"] < GRAVIDADE_REFERENCIA:
        posicao_media = "abaixo"
    elif estatisticas["media"] > GRAVIDADE_REFERENCIA:
        posicao_media = "acima"
    else:
        posicao_media = "igual"

    if len(valores) == 1:
        tendencia = "O gráfico contém apenas um ponto experimental."
    else:
        amplitude = estatisticas["maximo"] - estatisticas["minimo"]
        if amplitude <= 0.4:
            tendencia = "Os pontos estão bastante próximos entre si, indicando pouca variação entre as medições."
        elif amplitude <= 1.6:
            tendencia = "Os pontos apresentam variação moderada ao longo das medições."
        else:
            tendencia = "Os pontos apresentam variação ampla, indicando diferenças importantes entre as medições."

    return (
        f"Audiodescrição do gráfico. O eixo horizontal representa o número da medição e o eixo vertical representa "
        f"a aceleração da gravidade em metros por segundo ao quadrado. Há {estatisticas['n']} pontos experimentais. "
        f"O menor valor é {estatisticas['minimo']:.4f}, na medição {indice_min}, e o maior valor é "
        f"{estatisticas['maximo']:.4f}, na medição {indice_max}. A média experimental é "
        f"{estatisticas['media']:.4f}, ficando {posicao_media} da linha de referência de "
        f"{GRAVIDADE_REFERENCIA:.5f}. {tendencia}"
    )


def parecer_pedagogico_acessivel(estatisticas):
    if estatisticas["n"] == 0:
        return (
            "Parecer pedagógico: registre pelo menos uma medição para que o sistema possa comparar o resultado "
            "experimental com o valor de referência da gravidade."
        )

    if estatisticas["erro_percentual"] <= 5:
        recomendacao = (
            "O resultado apresenta excelente aproximação. Compare as repetições e discuta quais cuidados "
            "experimentais ajudaram a obter valores tão próximos da referência."
        )
    elif estatisticas["erro_percentual"] <= 10:
        recomendacao = (
            "O resultado apresenta boa aproximação. Vale repetir algumas medidas e observar como o controle do "
            "tempo, das distâncias e da montagem pode reduzir ainda mais o erro."
        )
    elif estatisticas["erro_percentual"] <= 20:
        recomendacao = (
            "O resultado apresenta diferença perceptível em relação à referência. Recomenda-se revisar o "
            "procedimento, repetir as medidas e identificar possíveis fontes de incerteza experimental."
        )
    else:
        recomendacao = (
            "O resultado está distante do valor esperado. Antes de concluir o experimento, revise unidades, "
            "instrumentos, montagem e forma de medir o tempo e repita o procedimento."
        )

    return f"Parecer pedagógico: {recomendacao}"


def gerar_relatorio_acessivel(experimento, configuracao):
    dados = configuracao["dados"]
    estatisticas = calcular_estatisticas(dados)
    medicoes = descrever_medicoes_para_audio(experimento, dados)

    abertura = (
        f"Relatório acessível do experimento {configuracao['titulo']}. "
        f"O valor de referência adotado para a gravidade é {GRAVIDADE_REFERENCIA:.5f} metros por segundo ao quadrado."
    )

    if estatisticas["n"] == 0:
        resultado = "Ainda não há resultados experimentais para análise."
    else:
        resultado = (
            f"Foram registradas {estatisticas['n']} medições. A média obtida foi {estatisticas['media']:.4f} metros "
            f"por segundo ao quadrado. O desvio padrão foi {estatisticas['desvio_padrao']:.4f}. "
            f"O erro percentual médio foi {estatisticas['erro_percentual']:.2f} por cento. "
            f"A qualidade experimental foi classificada como {estatisticas['qualidade']}."
        )

    grafico = audiodescrever_grafico(dados, estatisticas)
    interpretacao = interpretar_resultado(estatisticas)
    parecer = parecer_pedagogico_acessivel(estatisticas)

    secoes = {
        "abertura": abertura,
        "medicoes": medicoes,
        "resultado": resultado,
        "audiodescricao_grafico": grafico,
        "interpretacao": interpretacao,
        "parecer_pedagogico": parecer,
    }

    texto_completo = " ".join([abertura] + medicoes + [resultado, grafico, interpretacao, parecer])

    return {
        "experimento": experimento,
        "titulo": configuracao["titulo"],
        "estatisticas": estatisticas,
        "secoes": secoes,
        "texto_completo": texto_completo,
    }


def gerar_grafico_resultados(dados, estatisticas, titulo_experimento):
    valores_g = [float(item["gravidade"]) for item in dados if "gravidade" in item]
    if not valores_g:
        return None

    medicoes = list(range(1, len(valores_g) + 1))
    arquivo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    caminho = arquivo.name
    arquivo.close()

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(medicoes, valores_g, marker="o", linewidth=2, markersize=7, label="g experimental")
    ax.axhline(GRAVIDADE_REFERENCIA, linestyle="--", linewidth=2, label=f"g de referência = {GRAVIDADE_REFERENCIA:.3f} m/s²")

    if estatisticas["media"] is not None:
        ax.axhline(estatisticas["media"], linestyle=":", linewidth=2, label=f"média experimental = {estatisticas['media']:.3f} m/s²")

    for indice, valor in zip(medicoes, valores_g):
        ax.annotate(f"{valor:.2f}", (indice, valor), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

    ax.set_title(f"Resultado experimental — {titulo_experimento}", fontsize=14, fontweight="bold")
    ax.set_xlabel("Número da medição")
    ax.set_ylabel("Aceleração da gravidade, g (m/s²)")
    ax.set_xticks(medicoes)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)

    todos_valores = valores_g + [GRAVIDADE_REFERENCIA]
    if estatisticas["media"] is not None:
        todos_valores.append(estatisticas["media"])
    minimo = min(todos_valores)
    maximo = max(todos_valores)
    margem = max((maximo - minimo) * 0.18, 0.6)
    ax.set_ylim(minimo - margem, maximo + margem)

    fig.tight_layout()
    fig.savefig(caminho, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return caminho


def escrever_titulo_secao(pdf, titulo):
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(7, 26, 47)
    pdf.cell(0, 9, titulo, ln=True)
    pdf.set_text_color(0, 0, 0)


def atualizar_resultado_persistido(grupo_id, chave_experimento, dados):
    if not grupo_id:
        return
    estatisticas = calcular_estatisticas(dados)
    try:
        salvar_resultado(grupo_id, chave_experimento, estatisticas, interpretar_resultado(estatisticas))
    except Exception:
        pass


@app.route("/")
def index():
    grupo_id = request.args.get("grupo_id", "").strip()
    contexto = None
    mensagem_banco = ""

    if grupo_id:
        try:
            contexto = obter_contexto_grupo(grupo_id)
        except Exception:
            contexto = None
            mensagem_banco = "Não foi possível carregar o contexto persistido do banco."

    queda = dados_persistidos(grupo_id, "queda") if grupo_id else None
    pendulo = dados_persistidos(grupo_id, "pendulo") if grupo_id else None
    plano = dados_persistidos(grupo_id, "plano") if grupo_id else None

    dados_q = queda if queda is not None else dados_queda
    dados_p = pendulo if pendulo is not None else dados_pendulo
    dados_pl = plano if plano is not None else dados_plano

    return render_template(
        "index.html",
        mensagem_voz="Bem-vindo ao Laboratório de Física Acessível.",
        grupo_id=grupo_id,
        contexto=contexto,
        mensagem_banco=mensagem_banco,
        dados_queda=dados_q,
        dados_pendulo=dados_p,
        dados_plano=dados_pl,
        estatisticas_queda=calcular_estatisticas(dados_q),
        estatisticas_pendulo=calcular_estatisticas(dados_p),
        estatisticas_plano=calcular_estatisticas(dados_pl),
    )


@app.route("/api/health/supabase")
def api_health_supabase():
    resultado = verificar_conexao_supabase()
    return jsonify(resultado), 200 if resultado.get("ok") else 503


@app.route("/salvar-grupo", methods=["POST"])
def salvar_grupo():
    nomes = [request.form.get(f"nome{i}", "").strip() for i in range(1, 6)]
    grupo_local = {"nomes": nomes, "turma": request.form.get("turma", ""), "serie": request.form.get("serie", "")}
    with open(CAMINHO_GRUPO, "w", encoding="utf-8") as arquivo:
        json.dump(grupo_local, arquivo, ensure_ascii=False, indent=2)

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
        "componente_curricular": request.form.get("componente_curricular", "Física"),
        "professor_responsavel": request.form.get("professor_responsavel", ""),
        "codigo_grupo": request.form.get("codigo_grupo", "Grupo 1"),
    }

    try:
        contexto = cadastrar_contexto_escolar(payload)
        return redirect(f"/?grupo_id={contexto['grupo']['id']}")
    except Exception as exc:
        return f"Não foi possível salvar o contexto escolar no banco: {exc}", 500


@app.route("/queda-livre", methods=["POST"])
def queda_livre():
    try:
        altura = parse_numero(request.form["altura"])
        tempo = parse_numero(request.form["tempo"])
    except ValueError:
        return "Informe valores numéricos válidos para altura e tempo.", 400

    if altura <= 0 or tempo <= 0:
        return "Altura e tempo devem ser maiores que zero.", 400

    g = 2 * altura / (tempo**2)
    item = {"altura": altura, "tempo": tempo, "gravidade": round(g, 4)}
    grupo_id = request.form.get("grupo_id", "").strip()

    if grupo_id:
        registrar_medicao(grupo_id, "queda", {"altura_m": altura, "tempo_s": tempo, "gravidade_m_s2": round(g, 4)}, "manual")
        dados = dados_persistidos(grupo_id, "queda") or [item]
        atualizar_resultado_persistido(grupo_id, "queda", dados)
        return redirect(f"/?grupo_id={grupo_id}")

    dados_queda.append(item)
    return redirect("/")


@app.route("/pendulo", methods=["POST"])
def pendulo():
    try:
        comprimento = parse_numero(request.form["comprimento"])
        periodo = parse_numero(request.form["periodo"])
    except ValueError:
        return "Informe valores numéricos válidos para comprimento e período.", 400

    if comprimento <= 0 or periodo <= 0:
        return "Comprimento e período devem ser maiores que zero.", 400

    g = (4 * math.pi**2 * comprimento) / (periodo**2)
    item = {"comprimento": comprimento, "periodo": periodo, "gravidade": round(g, 4)}
    grupo_id = request.form.get("grupo_id", "").strip()

    if grupo_id:
        registrar_medicao(grupo_id, "pendulo", {"comprimento_m": comprimento, "periodo_s": periodo, "gravidade_m_s2": round(g, 4)}, "manual")
        dados = dados_persistidos(grupo_id, "pendulo") or [item]
        atualizar_resultado_persistido(grupo_id, "pendulo", dados)
        return redirect(f"/?grupo_id={grupo_id}")

    dados_pendulo.append(item)
    return redirect("/")


@app.route("/plano", methods=["POST"])
def plano():
    try:
        angulo = parse_numero(request.form["angulo"])
        distancia = parse_numero(request.form["distancia"])
        tempo = parse_numero(request.form["tempo"])
    except ValueError:
        return "Informe valores numéricos válidos para ângulo, distância e tempo.", 400

    if angulo <= 0 or angulo >= 90:
        return "O ângulo deve estar entre 0 e 90 graus.", 400
    if distancia <= 0 or tempo <= 0:
        return "Distância e tempo devem ser maiores que zero.", 400

    aceleracao = 2 * distancia / (tempo**2)
    g = aceleracao / math.sin(math.radians(angulo))
    item = {"angulo": angulo, "distancia": distancia, "tempo": tempo, "aceleracao": round(aceleracao, 4), "gravidade": round(g, 4)}
    grupo_id = request.form.get("grupo_id", "").strip()

    if grupo_id:
        registrar_medicao(
            grupo_id,
            "plano",
            {
                "angulo_graus": angulo,
                "distancia_m": distancia,
                "tempo_s": tempo,
                "aceleracao_m_s2": round(aceleracao, 4),
                "gravidade_m_s2": round(g, 4),
            },
            "manual",
        )
        dados = dados_persistidos(grupo_id, "plano") or [item]
        atualizar_resultado_persistido(grupo_id, "plano", dados)
        return redirect(f"/?grupo_id={grupo_id}")

    dados_plano.append(item)
    return redirect("/")


@app.route("/limpar-<experimento>", methods=["POST"])
def limpar_experimento(experimento):
    grupo_id = request.form.get("grupo_id", "").strip()
    if experimento not in ("queda", "pendulo", "plano"):
        return jsonify({"erro": "Experimento inválido"}), 404

    if grupo_id:
        limpar_medicoes(grupo_id, experimento)
        return redirect(f"/?grupo_id={grupo_id}")

    if experimento == "queda":
        dados_queda.clear()
    elif experimento == "pendulo":
        dados_pendulo.clear()
    elif experimento == "plano":
        dados_plano.clear()
    return redirect("/")


@app.route("/api/estatisticas/<experimento>")
def api_estatisticas(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    configuracao = obter_configuracao_experimento(experimento, grupo_id)
    if not configuracao:
        return jsonify({"erro": "Experimento inválido"}), 404

    estatisticas = calcular_estatisticas(configuracao["dados"])
    return jsonify({"experimento": experimento, "estatisticas": estatisticas, "interpretacao": interpretar_resultado(estatisticas)})


@app.route("/api/relatorio-acessivel/<experimento>")
def api_relatorio_acessivel(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    configuracao = obter_configuracao_experimento(experimento, grupo_id)
    if not configuracao:
        return jsonify({"erro": "Experimento inválido"}), 404
    return jsonify(gerar_relatorio_acessivel(experimento, configuracao))


@app.route("/relatorio/<experimento>")
def gerar_pdf(experimento):
    grupo_id = request.args.get("grupo_id", "").strip()
    configuracao = obter_configuracao_experimento(experimento, grupo_id)
    if not configuracao:
        return "Experimento não identificado.", 404

    contexto = obter_contexto_grupo(grupo_id) if grupo_id else None
    if contexto:
        turma_db = contexto.get("turma") or {}
        escola_db = contexto.get("escola") or {}
        grupo_db = contexto.get("grupo") or {}
        grupo = {
            "nomes": [p.get("nome_exibicao", "") for p in contexto.get("participantes", [])],
            "turma": turma_db.get("turma", ""),
            "serie": turma_db.get("serie_ano", ""),
            "escola": escola_db.get("nome", ""),
            "codigo_grupo": grupo_db.get("codigo_grupo", ""),
        }
    else:
        if not os.path.exists(CAMINHO_GRUPO):
            return "Grupo não cadastrado", 400
        with open(CAMINHO_GRUPO, encoding="utf-8") as arquivo:
            grupo = json.load(arquivo)

    dados = configuracao["dados"]
    estatisticas = calcular_estatisticas(dados)
    interpretacao = interpretar_resultado(estatisticas)
    caminho_grafico = gerar_grafico_resultados(dados, estatisticas, configuracao["titulo"])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(7, 26, 47)
    pdf.rect(0, 0, 210, 32, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 16)
    pdf.set_xy(12, 8)
    pdf.cell(0, 8, "Física Web", ln=True)
    pdf.set_x(12)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 7, f"Relatório Experimental — {configuracao['titulo']}", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(39)

    pdf.set_font("Arial", "", 10)
    if grupo.get("escola"):
        pdf.cell(0, 7, f"Escola: {grupo.get('escola', '')}", ln=True)
    pdf.cell(0, 7, f"Turma: {grupo.get('turma', '')}    Série: {grupo.get('serie', '')}", ln=True)
    if grupo.get("codigo_grupo"):
        pdf.cell(0, 7, f"Grupo: {grupo.get('codigo_grupo', '')}", ln=True)
    integrantes = [nome for nome in grupo.get("nomes", []) if nome]
    if integrantes:
        pdf.multi_cell(0, 6, "Integrantes: " + ", ".join(integrantes))

    pdf.ln(3)
    escrever_titulo_secao(pdf, "1. Referencial teórico")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, configuracao["teoria"])

    pdf.ln(3)
    escrever_titulo_secao(pdf, "2. Resultado principal")

    if estatisticas["n"] == 0:
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 7, "Ainda não há medidas registradas para análise.")
    else:
        pdf.set_fill_color(235, 244, 255)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(95, 12, f"g médio = {estatisticas['media']:.4f} m/s2", border=0, fill=True)
        pdf.cell(95, 12, f"Erro = {estatisticas['erro_percentual']:.2f}%", border=0, ln=True, fill=True)
        pdf.set_font("Arial", "", 10)
        pdf.cell(95, 10, f"Referência = {GRAVIDADE_REFERENCIA:.5f} m/s2", border=0, fill=True)
        pdf.cell(95, 10, f"Qualidade = {estatisticas['qualidade']}", border=0, ln=True, fill=True)
        pdf.ln(4)
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 6, interpretacao)

    if caminho_grafico and os.path.exists(caminho_grafico):
        pdf.ln(4)
        escrever_titulo_secao(pdf, "3. Leitura visual dos resultados")
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 5, "Cada ponto representa uma medição de g. A linha tracejada indica o valor de referência e a linha pontilhada mostra a média experimental. Quanto mais próximos os pontos estiverem da referência, menor é o erro do experimento.")
        pdf.ln(2)
        pdf.image(caminho_grafico, x=15, w=180)

    if dados:
        pdf.ln(5)
        escrever_titulo_secao(pdf, "4. Indicadores estatísticos")
        pdf.set_font("Arial", "", 9)
        linhas_estatisticas = [
            ("Número de medidas", estatisticas["n"]),
            ("Média experimental de g (m/s2)", f"{estatisticas['media']:.4f}"),
            ("Valor mínimo de g (m/s2)", f"{estatisticas['minimo']:.4f}"),
            ("Valor máximo de g (m/s2)", f"{estatisticas['maximo']:.4f}"),
            ("Desvio padrão amostral (m/s2)", f"{estatisticas['desvio_padrao']:.4f}"),
            ("Erro percentual médio", f"{estatisticas['erro_percentual']:.2f}%"),
        ]
        for rotulo, valor in linhas_estatisticas:
            pdf.cell(105, 7, str(rotulo), border=1)
            pdf.cell(75, 7, str(valor), border=1, ln=True)

        pdf.ln(5)
        escrever_titulo_secao(pdf, "5. Dados experimentais")
        pdf.set_font("Arial", "", 8)
        colunas = list(dados[0].keys())
        largura = 180 / max(len(colunas), 1)
        for coluna in colunas:
            pdf.set_font("Arial", "B", 8)
            pdf.cell(largura, 7, coluna.title(), border=1)
        pdf.ln()
        pdf.set_font("Arial", "", 8)
        for entrada in dados:
            for coluna in colunas:
                pdf.cell(largura, 7, str(entrada.get(coluna, "")), border=1)
            pdf.ln()

    buffer = io.BytesIO()
    conteudo_pdf = pdf.output(dest="S")
    if isinstance(conteudo_pdf, str):
        conteudo_pdf = conteudo_pdf.encode("latin-1")
    buffer.write(conteudo_pdf)
    buffer.seek(0)

    if caminho_grafico and os.path.exists(caminho_grafico):
        try:
            os.remove(caminho_grafico)
        except OSError:
            pass

    return send_file(buffer, as_attachment=True, download_name=f"relatorio_{experimento}.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)
