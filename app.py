from flask import Flask, render_template, request, redirect, jsonify, send_file, url_for
import io
import json
import math
import os
import statistics

from fpdf import FPDF
import matplotlib.pyplot as plt


app = Flask(__name__)

dados_queda = []
dados_pendulo = []
dados_plano = []

CAMINHO_GRUPO = "grupo_Leandro.json"
GRAVIDADE_REFERENCIA = 9.80665


def classificar_qualidade(erro_percentual):
    """Classifica a qualidade experimental a partir do erro percentual médio."""
    if erro_percentual is None:
        return "Dados insuficientes"
    if erro_percentual <= 5:
        return "Excelente"
    if erro_percentual <= 10:
        return "Boa"
    if erro_percentual <= 20:
        return "Regular"
    return "Requer revisão experimental"


def calcular_estatisticas(dados):
    """Calcula indicadores estatísticos para uma coleção de medidas de gravidade."""
    valores_g = [float(item["gravidade"]) for item in dados if "gravidade" in item]

    if not valores_g:
        return {
            "n": 0,
            "media": None,
            "desvio_padrao": None,
            "erro_percentual": None,
            "qualidade": "Dados insuficientes",
            "gravidade_referencia": GRAVIDADE_REFERENCIA,
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
    }


def obter_configuracao_experimento(experimento):
    configuracoes = {
        "queda": {
            "dados": dados_queda,
            "x_label": "tempo",
            "y_label": "altura",
            "titulo": "Queda Livre",
            "teoria": (
                "A queda livre é um movimento uniformemente acelerado sob ação da gravidade. "
                "Desprezando a resistência do ar e considerando velocidade inicial nula, "
                "a aceleração gravitacional pode ser estimada pela relação g = 2h/t²."
            ),
        },
        "pendulo": {
            "dados": dados_pendulo,
            "x_label": "periodo",
            "y_label": "gravidade",
            "titulo": "Pêndulo Simples",
            "teoria": (
                "Para pequenas oscilações, o período de um pêndulo simples depende do "
                "comprimento do fio e da aceleração da gravidade. A estimativa experimental "
                "é obtida pela relação g = 4π²L/T²."
            ),
        },
        "plano": {
            "dados": dados_plano,
            "x_label": "tempo",
            "y_label": "gravidade",
            "titulo": "Plano Inclinado",
            "teoria": (
                "Em um plano inclinado ideal, a componente da aceleração paralela ao plano "
                "é a = g sen(θ). A partir da distância percorrida e do tempo, estima-se a "
                "aceleração e, consequentemente, o valor experimental de g."
            ),
        },
    }
    return configuracoes.get(experimento)


@app.route("/")
def index():
    mensagem_voz = (
        "Bem-vindo ao Laboratório de Física Acessível. Use Tab para navegar. "
        "Pressione Ctrl+Q, Ctrl+P ou Ctrl+L para áudio dos experimentos."
    )
    return render_template(
        "index.html",
        mensagem_voz=mensagem_voz,
        dados_queda=dados_queda,
        dados_pendulo=dados_pendulo,
        dados_plano=dados_plano,
        estatisticas_queda=calcular_estatisticas(dados_queda),
        estatisticas_pendulo=calcular_estatisticas(dados_pendulo),
        estatisticas_plano=calcular_estatisticas(dados_plano),
    )


@app.route("/salvar-grupo", methods=["POST"])
def salvar_grupo():
    grupo = {
        "nomes": [request.form.get(f"nome{i}", "") for i in range(1, 6)],
        "turma": request.form.get("turma", ""),
        "serie": request.form.get("serie", ""),
    }
    with open(CAMINHO_GRUPO, "w", encoding="utf-8") as arquivo:
        json.dump(grupo, arquivo, ensure_ascii=False, indent=2)
    return redirect("/")


@app.route("/queda-livre", methods=["POST"])
def queda_livre():
    altura = float(request.form["altura"])
    tempo = float(request.form["tempo"])

    if altura <= 0 or tempo <= 0:
        return "Altura e tempo devem ser maiores que zero.", 400

    g = 2 * altura / (tempo**2)
    dados_queda.append(
        {
            "altura": altura,
            "tempo": tempo,
            "gravidade": round(g, 4),
        }
    )
    return redirect("/")


@app.route("/pendulo", methods=["POST"])
def pendulo():
    comprimento = float(request.form["comprimento"])
    periodo = float(request.form["periodo"])

    if comprimento <= 0 or periodo <= 0:
        return "Comprimento e período devem ser maiores que zero.", 400

    g = (4 * math.pi**2 * comprimento) / (periodo**2)
    dados_pendulo.append(
        {
            "comprimento": comprimento,
            "periodo": periodo,
            "gravidade": round(g, 4),
        }
    )
    return redirect("/")


@app.route("/plano", methods=["POST"])
def plano():
    angulo = float(request.form["angulo"])
    distancia = float(request.form["distancia"])
    tempo = float(request.form["tempo"])

    if angulo <= 0 or angulo >= 90:
        return "O ângulo deve estar entre 0° e 90°.", 400
    if distancia <= 0 or tempo <= 0:
        return "Distância e tempo devem ser maiores que zero.", 400

    aceleracao = 2 * distancia / (tempo**2)
    g = aceleracao / math.sin(math.radians(angulo))
    dados_plano.append(
        {
            "angulo": angulo,
            "distancia": distancia,
            "tempo": tempo,
            "aceleracao": round(aceleracao, 4),
            "gravidade": round(g, 4),
        }
    )
    return redirect("/")


@app.route("/limpar-<experimento>", methods=["POST"])
def limpar_experimento(experimento):
    if experimento == "queda":
        dados_queda.clear()
    elif experimento == "pendulo":
        dados_pendulo.clear()
    elif experimento == "plano":
        dados_plano.clear()
    else:
        return jsonify({"erro": "Experimento inválido"}), 404

    return redirect("/")


@app.route("/api/estatisticas/<experimento>")
def api_estatisticas(experimento):
    configuracao = obter_configuracao_experimento(experimento)
    if not configuracao:
        return jsonify({"erro": "Experimento inválido"}), 404

    return jsonify(
        {
            "experimento": experimento,
            "estatisticas": calcular_estatisticas(configuracao["dados"]),
        }
    )


@app.route("/relatorio/<experimento>")
def gerar_pdf(experimento):
    configuracao = obter_configuracao_experimento(experimento)
    if not configuracao:
        return "Experimento não identificado.", 404

    if not os.path.exists(CAMINHO_GRUPO):
        return "Grupo não cadastrado", 400

    with open(CAMINHO_GRUPO, encoding="utf-8") as arquivo:
        grupo = json.load(arquivo)

    dados = configuracao["dados"]
    estatisticas = calcular_estatisticas(dados)
    caminho_grafico = None

    if dados:
        x_label = configuracao["x_label"]
        y_label = configuracao["y_label"]
        x = [d[x_label] for d in dados if x_label in d]
        y = [d[y_label] for d in dados if y_label in d]

        if x and y and len(x) == len(y):
            caminho_grafico = "grafico.png"
            plt.figure()
            plt.plot(x, y, marker="o")
            plt.title(f"{y_label.title()} em função de {x_label.title()}")
            plt.xlabel(x_label.title())
            plt.ylabel(y_label.title())
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(caminho_grafico)
            plt.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Relatório Experimental - {configuracao['titulo']}", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Turma: {grupo.get('turma', '')} - Série: {grupo.get('serie', '')}", ln=True)
    pdf.cell(0, 8, "Integrantes:", ln=True)
    for nome in grupo.get("nomes", []):
        if nome:
            pdf.cell(0, 7, f"- {nome}", ln=True)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 9, "Referencial Teórico", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 7, configuracao["teoria"])

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 9, "Análise Estatística Automática", ln=True)
    pdf.set_font("Arial", "", 10)

    if estatisticas["n"] == 0:
        pdf.multi_cell(0, 7, "Ainda não há medidas registradas para análise estatística.")
    else:
        linhas_estatisticas = [
            ("Número de medidas", estatisticas["n"]),
            ("Gravidade de referência (m/s²)", f"{estatisticas['gravidade_referencia']:.5f}"),
            ("Média experimental de g (m/s²)", f"{estatisticas['media']:.4f}"),
            ("Desvio padrão amostral (m/s²)", f"{estatisticas['desvio_padrao']:.4f}"),
            ("Erro percentual médio", f"{estatisticas['erro_percentual']:.2f}%"),
            ("Qualidade experimental", estatisticas["qualidade"]),
        ]

        for rotulo, valor in linhas_estatisticas:
            pdf.cell(85, 8, str(rotulo), border=1)
            pdf.cell(85, 8, str(valor), border=1, ln=True)

    if dados:
        pdf.ln(6)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 9, "Dados Experimentais", ln=True)
        pdf.set_font("Arial", "", 9)

        colunas = list(dados[0].keys())
        largura = max(25, min(45, 180 / max(len(colunas), 1)))

        for coluna in colunas:
            pdf.cell(largura, 8, coluna.title(), border=1)
        pdf.ln()

        for entrada in dados:
            for coluna in colunas:
                pdf.cell(largura, 8, str(entrada.get(coluna, "")), border=1)
            pdf.ln()

    if caminho_grafico and os.path.exists(caminho_grafico):
        pdf.ln(8)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 9, "Representação Gráfica", ln=True)
        pdf.image(caminho_grafico, x=15, w=175)

    buffer = io.BytesIO()
    conteudo_pdf = pdf.output(dest="S")
    if isinstance(conteudo_pdf, str):
        conteudo_pdf = conteudo_pdf.encode("latin-1")
    buffer.write(conteudo_pdf)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"relatorio_{experimento}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    app.run(debug=True)
