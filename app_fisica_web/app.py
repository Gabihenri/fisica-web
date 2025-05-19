from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import io
import csv
from math import sin, radians
from datetime import datetime
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os

app = Flask(__name__)

dados_queda = []
dados_pendulo = []
dados_plano = []

@app.route("/")
def index():
    mensagem_voz = "Bem-vindo ao Laboratório de Física Acessível. Pressione Control Q para acessar Queda Livre, Control P para Pêndulo, Control L para Plano Inclinado. Passe o mouse sobre os botões para ouvir as instruções."
    return render_template("index.html",
                           dados_queda=dados_queda,
                           dados_pendulo=dados_pendulo,
                           dados_plano=dados_plano,
                           mensagem_voz=mensagem_voz)

@app.route("/queda-livre", methods=["POST"])
def queda_livre():
    altura = float(request.form["altura"])
    tempo = float(request.form["tempo"])
    g = round((2 * altura) / (tempo ** 2), 2)
    dados_queda.append({"altura": altura, "tempo": tempo, "gravidade": g})
    return redirect(url_for("index"))

@app.route("/pendulo", methods=["POST"])
def pendulo():
    comprimento = float(request.form["comprimento"])
    periodo = float(request.form["periodo"])
    g = round((4 * 3.14 ** 2 * comprimento) / (periodo ** 2), 2)
    dados_pendulo.append({"comprimento": comprimento, "periodo": periodo, "gravidade": g})
    return redirect(url_for("index"))

@app.route("/plano", methods=["POST"])
def plano():
    angulo = float(request.form["angulo"])
    distancia = float(request.form["distancia"])
    tempo = float(request.form["tempo"])
    g = round((2 * distancia) / (tempo ** 2 * sin(radians(angulo))), 2)
    dados_plano.append({"angulo": angulo, "distancia": distancia, "tempo": tempo, "gravidade": g})
    return redirect(url_for("index"))

@app.route("/limpar-queda", methods=["POST"])
def limpar_queda():
    dados_queda.clear()
    return redirect(url_for("index"))

@app.route("/limpar-pendulo", methods=["POST"])
def limpar_pendulo():
    dados_pendulo.clear()
    return redirect(url_for("index"))

@app.route("/limpar-plano", methods=["POST"])
def limpar_plano():
    dados_plano.clear()
    return redirect(url_for("index"))

@app.route("/exportar/<experimento>")
def exportar(experimento):
    formato = request.args.get("formato", "csv")
    output = io.StringIO()

    if experimento == "queda":
        cabecalho = ["Altura (m)", "Tempo (s)", "Gravidade (m/s²)"]
        dados = [[d["altura"], d["tempo"], d["gravidade"]] for d in dados_queda]
    elif experimento == "pendulo":
        cabecalho = ["Comprimento (m)", "Período (s)", "Gravidade (m/s²)"]
        dados = [[d["comprimento"], d["periodo"], d["gravidade"]] for d in dados_pendulo]
    elif experimento == "plano":
        cabecalho = ["Ângulo (°)", "Distância (m)", "Tempo (s)", "Gravidade (m/s²)"]
        dados = [[d["angulo"], d["distancia"], d["tempo"], d["gravidade"]] for d in dados_plano]
    else:
        return "Experimento inválido", 400

    if formato == "csv":
        writer = csv.writer(output)
        writer.writerow(cabecalho)
        writer.writerows(dados)
        mimetype = "text/csv"
        ext = "csv"
    elif formato == "txt":
        output.write("\t".join(cabecalho) + "\n")
        for linha in dados:
            output.write("\t".join(str(c) for c in linha) + "\n")
        mimetype = "text/plain"
        ext = "txt"
    else:
        return "Formato inválido", 400

    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()),
                     mimetype=mimetype,
                     as_attachment=True,
                     download_name=f"{experimento}_dados.{ext}")

@app.route("/dados/<experimento>")
def dados_experimento(experimento):
    if experimento == "queda":
        return jsonify(dados=dados_queda)
    elif experimento == "pendulo":
        return jsonify(dados=dados_pendulo)
    elif experimento == "plano":
        return jsonify(dados=dados_plano)
    return {}, 404

@app.route("/relatorio/<experimento>")
def gerar_relatorio(experimento):
    if experimento == "queda":
        dados = dados_queda
        titulo = "Relatório de Queda Livre"
        colunas = ["Altura (m)", "Tempo (s)", "Gravidade (m/s²)"]
        y = [d['altura'] for d in dados]
        x = [d['tempo'] for d in dados]
    elif experimento == "pendulo":
        dados = dados_pendulo
        titulo = "Relatório de Pêndulo Simples"
        colunas = ["Comprimento (m)", "Período (s)", "Gravidade (m/s²)"]
        y = [d['comprimento'] for d in dados]
        x = [d['periodo'] for d in dados]
    elif experimento == "plano":
        dados = dados_plano
        titulo = "Relatório de Plano Inclinado"
        colunas = ["Ângulo (°)", "Distância (m)", "Tempo (s)", "Gravidade (m/s²)"]
        y = [d['distancia'] for d in dados]
        x = [d['tempo'] for d in dados]
    else:
        return "Experimento inválido", 400

    if not dados:
        return "Sem dados para gerar o relatório.", 400

    # Gera gráfico com matplotlib
    plt.figure()
    plt.plot(x, y, marker='o')
    plt.title(titulo)
    plt.xlabel("Tempo (s)" if experimento != "pendulo" else "Período (s)")
    plt.ylabel(colunas[0])
    plt.grid(True)
    nome_img = f"grafico_{experimento}.png"
    plt.savefig(nome_img)
    plt.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 50, titulo)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, height - 70, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Inserir gráfico
    pdf.drawImage(nome_img, 50, height - 350, width=500, preserveAspectRatio=True)

    # Inserir tabela
    dados_tabela = [colunas]
    for d in dados:
        linha = []
        for chave in colunas:
            key = chave.split(" ")[0].lower()
            linha.append(d.get(key, ""))
        dados_tabela.append(linha)

    t = Table(dados_tabela, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    t.wrapOn(pdf, width, height)
    t.drawOn(pdf, 50, height - 550)

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    os.remove(nome_img)

    return send_file(buffer, as_attachment=True, download_name=f"relatorio_{experimento}.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)
