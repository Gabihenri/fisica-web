from flask import Flask, render_template, request, redirect, jsonify, send_file, url_for
import json, os, io
from fpdf import FPDF
import matplotlib.pyplot as plt
import math

app = Flask(__name__)
dados_queda, dados_pendulo, dados_plano = [], [], []
CAMINHO_GRUPO = "grupo_Leandro.json"

@app.route("/")
def index():
    mensagem_voz = "Bem-vindo ao Laboratório de Física Acessível. Use Tab para navegar. Pressione Ctrl+Q, Ctrl+P ou Ctrl+L para áudio dos experimentos."
    return render_template("index.html", mensagem_voz=mensagem_voz,
                           dados_queda=dados_queda,
                           dados_pendulo=dados_pendulo,
                           dados_plano=dados_plano)

@app.route("/salvar-grupo", methods=["POST"])
def salvar_grupo():
    grupo = {
        "nomes": [request.form.get(f"nome{i}", "") for i in range(1, 6)],
        "turma": request.form.get("turma", ""),
        "serie": request.form.get("serie", "")
    }
    with open(CAMINHO_GRUPO, "w", encoding="utf-8") as f:
        json.dump(grupo, f, ensure_ascii=False, indent=2)
    return redirect("/")

@app.route("/queda-livre", methods=["POST"])
def queda_livre():
    altura = float(request.form["altura"])
    tempo = float(request.form["tempo"])
    g = 2 * altura / (tempo**2)
    dados_queda.append({"altura": altura, "tempo": tempo, "gravidade": round(g, 2)})
    return redirect("/")

@app.route("/pendulo", methods=["POST"])
def pendulo():
    comprimento = float(request.form["comprimento"])
    periodo = float(request.form["periodo"])
    g = (4 * math.pi ** 2 * comprimento) / (periodo ** 2)
    dados_pendulo.append({"comprimento": comprimento, "periodo": periodo, "gravidade": round(g, 2)})
    return redirect("/")

@app.route("/plano", methods=["POST"])
def plano():
    angulo = float(request.form["angulo"])
    distancia = float(request.form["distancia"])
    tempo = float(request.form["tempo"])
    aceleracao = 2 * distancia / (tempo ** 2)
    g = aceleracao / math.sin(math.radians(angulo))
    dados_plano.append({"angulo": angulo, "distancia": distancia, "tempo": tempo, "gravidade": round(g, 2)})
    return redirect("/")

@app.route("/limpar-<experimento>", methods=["POST"])
def limpar_experimento(experimento):
    if experimento == "queda": dados_queda.clear()
    elif experimento == "pendulo": dados_pendulo.clear()
    elif experimento == "plano": dados_plano.clear()
    return ("", 204)

@app.route("/relatorio/<experimento>")
def gerar_pdf(experimento):
    if not os.path.exists(CAMINHO_GRUPO): return "Grupo não cadastrado", 400
    with open(CAMINHO_GRUPO, encoding="utf-8") as f: grupo = json.load(f)
    dados, x_label, y_label = [], "", ""
    if experimento == "queda": dados, x_label, y_label = dados_queda, "tempo", "altura"
    elif experimento == "pendulo": dados, x_label, y_label = dados_pendulo, "periodo", "gravidade"
    elif experimento == "plano": dados, x_label, y_label = dados_plano, "tempo", "gravidade"

    if dados:
        x = [d[x_label] for d in dados if x_label in d]
        y = [d[y_label] for d in dados if y_label in d]
        plt.figure()
        plt.plot(x, y, marker='o')
        plt.title(f"{y_label.title()} em função de {x_label.title()}")
        plt.xlabel(x_label.title())
        plt.ylabel(y_label.title())
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("grafico.png")
        plt.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Relatório Experimental - {experimento.upper()}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Turma: {grupo['turma']} - Série: {grupo['serie']}", ln=True)
    pdf.cell(0, 10, "Integrantes:", ln=True)
    for nome in grupo["nomes"]:
        if nome: pdf.cell(0, 8, f"- {nome}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Referencial Teórico:", ln=True)
    pdf.set_font("Arial", "", 11)
    teoricos = {
        "queda": "A queda livre é um movimento uniformemente acelerado sob ação da gravidade.",
        "pendulo": "O pêndulo simples é um sistema oscilatório dependente do comprimento e da gravidade.",
        "plano": "No plano inclinado, a aceleração depende do ângulo e da decomposição da força peso."
    }
    pdf.multi_cell(0, 8, teoricos.get(experimento, "Experimento não identificado."))

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Tratamento Estatístico (preencher manualmente):", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(60, 10, "Erro percentual teórico:", border=1)
    pdf.cell(60, 10, "", border=1, ln=True)
    pdf.cell(60, 10, "Desvio padrão:", border=1)
    pdf.cell(60, 10, "", border=1, ln=True)
    pdf.cell(60, 10, "Observações:", border=1)
    pdf.cell(60, 10, "", border=1, ln=True)

    if dados:
        pdf.ln(10)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Dados Experimentais:", ln=True)
        pdf.set_font("Arial", "", 11)
        colunas = list(dados[0].keys())
        for coluna in colunas:
            pdf.cell(40, 8, coluna.title(), border=1)
        pdf.ln()
        for entrada in dados:
            for coluna in colunas:
                valor = str(entrada.get(coluna, ""))
                pdf.cell(40, 8, valor, border=1)
            pdf.ln()

    if os.path.exists("grafico.png"):
        pdf.ln(10)
        pdf.image("grafico.png", x=10, w=180)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"relatorio_{experimento}.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
