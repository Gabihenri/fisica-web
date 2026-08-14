from flask import Flask, render_template, request, redirect, jsonify, send_file
import json
import math
import os

from db import cadastrar_contexto_escolar, excluir_grupo_experimental, limpar_medicoes, listar_medicoes, obter_contexto_grupo, registrar_medicao, salvar_resultado, verificar_conexao_supabase
from report_engine import gerar_pdf_cientifico, _grafico_temp
from scientific_engine import GRAVIDADE_REFERENCIA, analisar_experimento

app = Flask(__name__)
dados_queda, dados_pendulo, dados_plano = [], [], []
CAMINHO_GRUPO = "grupo_Leandro.json"


def parse_numero(valor): return float(str(valor).strip().replace(",", "."))
def origem_requisicao():
    origem = request.form.get("origem", "manual").strip().lower()
    return origem if origem in {"manual", "arduino", "raspberry", "other"} else "manual"


def converter_medicoes_banco(chave, linhas):
    dados=[]
    for linha in linhas:
        if chave=="queda": dados.append({"altura":float(linha["altura_m"]),"tempo":float(linha["tempo_s"]),"gravidade":float(linha["gravidade_m_s2"])})
        elif chave=="pendulo": dados.append({"comprimento":float(linha["comprimento_m"]),"periodo":float(linha["periodo_s"]),"gravidade":float(linha["gravidade_m_s2"])})
        elif chave=="plano": dados.append({"angulo":float(linha["angulo_graus"]),"distancia":float(linha["distancia_m"]),"tempo":float(linha["tempo_s"]),"aceleracao":float(linha["aceleracao_m_s2"]),"gravidade":float(linha["gravidade_m_s2"])})
    return dados


def dados_persistidos(grupo_id,chave):
    if not grupo_id:return None
    try:return converter_medicoes_banco(chave,listar_medicoes(grupo_id,chave))
    except Exception:return None


def configuracao_experimento(chave,grupo_id=None):
    persistidos=dados_persistidos(grupo_id,chave)
    configs={
      "queda":{"dados":persistidos if persistidos is not None else dados_queda,"titulo":"Queda Livre","teoria":"A queda livre e um movimento uniformemente acelerado sob acao da gravidade. Desprezando a resistencia do ar e considerando velocidade inicial nula, a gravidade pode ser estimada por g = 2h/t^2."},
      "pendulo":{"dados":persistidos if persistidos is not None else dados_pendulo,"titulo":"Pendulo Simples","teoria":"Para pequenas oscilacoes, o periodo de um pendulo simples depende do comprimento e da aceleracao da gravidade. A estimativa e g = 4*pi^2*L/T^2."},
      "plano":{"dados":persistidos if persistidos is not None else dados_plano,"titulo":"Plano Inclinado","teoria":"Em um plano inclinado ideal, a componente da aceleracao paralela ao plano e a = g*sen(theta). A partir da distancia e do tempo estima-se a aceleracao e g."}}
    return configs.get(chave)


def atualizar_resultado_persistido(grupo_id,chave,dados):
    if not grupo_id:return
    a=analisar_experimento(chave,dados)
    try:salvar_resultado(grupo_id,chave,a["estatisticas"],a["interpretacao"])
    except Exception:pass


def relatorio_acessivel(chave,config):
    a=analisar_experimento(chave,config["dados"]);stats=a["estatisticas"];modelo=a["modelo"];medicoes=[]
    for i,item in enumerate(config["dados"],1):
        if chave=="queda":medicoes.append(f"Medicao {i}: altura {item['altura']} metros, tempo {item['tempo']} segundos, gravidade calculada {item['gravidade']:.4f} metros por segundo ao quadrado.")
        elif chave=="pendulo":medicoes.append(f"Medicao {i}: comprimento {item['comprimento']} metros, periodo {item['periodo']} segundos, gravidade calculada {item['gravidade']:.4f} metros por segundo ao quadrado.")
        else:medicoes.append(f"Medicao {i}: angulo {item['angulo']} graus, distancia {item['distancia']} metros, tempo {item['tempo']} segundos e gravidade calculada {item['gravidade']:.4f} metros por segundo ao quadrado.")
    if not medicoes:medicoes=["Nenhuma medicao foi registrada ate o momento."]
    resumo=(f"Foram analisadas {stats['n']} medicoes. A media de g foi {stats['media']:.4f} metros por segundo ao quadrado, com erro percentual de {stats['erro_percentual']:.2f} por cento. A classificacao experimental foi {stats['qualidade']}." if stats["n"] else "Ainda nao ha resultados experimentais suficientes para analise.")
    descricao=modelo.get("descricao_modelo") or ""
    if modelo.get("regressao"):descricao+=f" O ajuste linear apresentou coeficiente de determinacao R ao quadrado igual a {modelo['regressao']['r2']:.4f}."
    if modelo.get("gravidade_modelo") is not None:descricao+=f" A estimativa grafica de g foi {modelo['gravidade_modelo']:.4f} metros por segundo ao quadrado."
    parecer="Parecer pedagogico: compare o resultado com o modelo teorico, observe a dispersao das repeticoes e discuta fontes de incerteza como resolucao dos instrumentos, tempo de reacao e montagem experimental."
    abertura=f"Relatorio acessivel do experimento {config['titulo']}. O valor de referencia adotado para g e {GRAVIDADE_REFERENCIA:.5f} metros por segundo ao quadrado."
    texto=" ".join([abertura]+medicoes+[resumo,descricao,a["interpretacao"],parecer])
    return {"experimento":chave,"titulo":config["titulo"],"estatisticas":stats,"modelo":modelo,"secoes":{"abertura":abertura,"medicoes":medicoes,"resultado":resumo,"audiodescricao_grafico":descricao,"interpretacao":a["interpretacao"],"parecer_pedagogico":parecer},"texto_completo":texto}

@app.route("/acesso")
def acesso():
    return render_template("acesso.html")

@app.route("/")
def index():
    grupo_id=request.args.get("grupo_id","").strip();contexto=None;mensagem_banco=""
    if grupo_id:
        try:contexto=obter_contexto_grupo(grupo_id)
        except Exception:mensagem_banco="Nao foi possivel carregar o contexto persistido do banco."
    q=dados_persistidos(grupo_id,"queda") if grupo_id else None;p=dados_persistidos(grupo_id,"pendulo") if grupo_id else None;pl=dados_persistidos(grupo_id,"plano") if grupo_id else None
    dq=q if q is not None else dados_queda;dp=p if p is not None else dados_pendulo;dpl=pl if pl is not None else dados_plano
    return render_template("index.html",grupo_id=grupo_id,contexto=contexto,mensagem_banco=mensagem_banco,dados_queda=dq,dados_pendulo=dp,dados_plano=dpl,estatisticas_queda=analisar_experimento("queda",dq)["estatisticas"],estatisticas_pendulo=analisar_experimento("pendulo",dp)["estatisticas"],estatisticas_plano=analisar_experimento("plano",dpl)["estatisticas"])

@app.route("/api/health/supabase")
def api_health_supabase():
    r=verificar_conexao_supabase();return jsonify(r),200 if r.get("ok") else 503

@app.route("/salvar-grupo",methods=["POST"])
def salvar_grupo():
    nomes=[request.form.get(f"nome{i}","").strip() for i in range(1,6)]
    try:
        with open(CAMINHO_GRUPO,"w",encoding="utf-8") as f:json.dump({"nomes":nomes,"turma":request.form.get("turma",""),"serie":request.form.get("serie","")},f,ensure_ascii=False,indent=2)
    except OSError:pass
    payload={"nomes":nomes,"escola":request.form.get("escola",""),"rede":request.form.get("rede",""),"municipio":request.form.get("municipio",""),"estado":request.form.get("estado",""),"ano_letivo":request.form.get("ano_letivo",""),"serie":request.form.get("serie",""),"turma":request.form.get("turma",""),"turno":request.form.get("turno",""),"componente_curricular":request.form.get("componente_curricular","Fisica"),"professor_responsavel":request.form.get("professor_responsavel",""),"codigo_grupo":request.form.get("codigo_grupo","Grupo 1")}
    try:
        c=cadastrar_contexto_escolar(payload);return redirect(f"/?grupo_id={c['grupo']['id']}")
    except Exception as exc:return f"Nao foi possivel salvar o contexto escolar no banco: {exc}",500

@app.route("/excluir-grupo",methods=["POST"])
def excluir_grupo():
    gid=request.form.get("grupo_id","").strip(); confirmacao=request.form.get("confirmacao","")
    if not gid:return "Grupo não informado.",400
    if confirmacao!="EXCLUIR":return "Confirmação de exclusão inválida.",400
    try:
        excluir_grupo_experimental(gid)
        try:
            if os.path.exists(CAMINHO_GRUPO):os.remove(CAMINHO_GRUPO)
        except OSError:pass
        return redirect("/?grupo_excluido=1#contexto")
    except Exception as exc:return f"Não foi possível excluir o grupo: {exc}",500

@app.route("/queda-livre",methods=["POST"])
def queda_livre():
    try:altura=parse_numero(request.form["altura"]);tempo=parse_numero(request.form["tempo"])
    except ValueError:return "Informe valores numericos validos para altura e tempo.",400
    if altura<=0 or tempo<=0:return "Altura e tempo devem ser maiores que zero.",400
    g=2*altura/(tempo**2);item={"altura":altura,"tempo":tempo,"gravidade":round(g,5)};gid=request.form.get("grupo_id","").strip()
    if gid:
        registrar_medicao(gid,"queda",{"altura_m":altura,"tempo_s":tempo,"gravidade_m_s2":round(g,5)},origem_requisicao());dados=dados_persistidos(gid,"queda") or [item];atualizar_resultado_persistido(gid,"queda",dados);return redirect(f"/?grupo_id={gid}&experimento=queda#experimentos")
    dados_queda.append(item);return redirect("/?experimento=queda#experimentos")

@app.route("/pendulo",methods=["POST"])
def pendulo():
    try:c=parse_numero(request.form["comprimento"]);t=parse_numero(request.form["periodo"])
    except ValueError:return "Informe valores numericos validos para comprimento e periodo.",400
    if c<=0 or t<=0:return "Comprimento e periodo devem ser maiores que zero.",400
    g=4*math.pi**2*c/t**2;item={"comprimento":c,"periodo":t,"gravidade":round(g,5)};gid=request.form.get("grupo_id","").strip()
    if gid:
        registrar_medicao(gid,"pendulo",{"comprimento_m":c,"periodo_s":t,"gravidade_m_s2":round(g,5)},origem_requisicao());dados=dados_persistidos(gid,"pendulo") or [item];atualizar_resultado_persistido(gid,"pendulo",dados);return redirect(f"/?grupo_id={gid}&experimento=pendulo#experimentos")
    dados_pendulo.append(item);return redirect("/?experimento=pendulo#experimentos")

@app.route("/plano",methods=["POST"])
def plano():
    try:a=parse_numero(request.form["angulo"]);d=parse_numero(request.form["distancia"]);t=parse_numero(request.form["tempo"])
    except ValueError:return "Informe valores numericos validos para angulo, distancia e tempo.",400
    if a<=0 or a>=90:return "O angulo deve estar entre 0 e 90 graus.",400
    if d<=0 or t<=0:return "Distancia e tempo devem ser maiores que zero.",400
    acc=2*d/t**2;g=acc/math.sin(math.radians(a));item={"angulo":a,"distancia":d,"tempo":t,"aceleracao":round(acc,5),"gravidade":round(g,5)};gid=request.form.get("grupo_id","").strip()
    if gid:
        registrar_medicao(gid,"plano",{"angulo_graus":a,"distancia_m":d,"tempo_s":t,"aceleracao_m_s2":round(acc,5),"gravidade_m_s2":round(g,5)},origem_requisicao());dados=dados_persistidos(gid,"plano") or [item];atualizar_resultado_persistido(gid,"plano",dados);return redirect(f"/?grupo_id={gid}&experimento=plano#experimentos")
    dados_plano.append(item);return redirect("/?experimento=plano#experimentos")

@app.route("/limpar-<experimento>",methods=["POST"])
def limpar_experimento(experimento):
    if experimento not in ("queda","pendulo","plano"):return jsonify({"erro":"Experimento invalido"}),404
    gid=request.form.get("grupo_id","").strip()
    if gid:limpar_medicoes(gid,experimento);return redirect(f"/?grupo_id={gid}&experimento={experimento}#experimentos")
    {"queda":dados_queda,"pendulo":dados_pendulo,"plano":dados_plano}[experimento].clear();return redirect(f"/?experimento={experimento}#experimentos")

@app.route("/api/analise/<experimento>")
def api_analise(experimento):
    c=configuracao_experimento(experimento,request.args.get("grupo_id","").strip());return (jsonify(analisar_experimento(experimento,c["dados"])) if c else (jsonify({"erro":"Experimento invalido"}),404))

@app.route("/api/estatisticas/<experimento>")
def api_estatisticas(experimento):
    c=configuracao_experimento(experimento,request.args.get("grupo_id","").strip())
    if not c:return jsonify({"erro":"Experimento invalido"}),404
    a=analisar_experimento(experimento,c["dados"]);return jsonify({"experimento":experimento,"estatisticas":a["estatisticas"],"interpretacao":a["interpretacao"]})

@app.route("/api/relatorio-acessivel/<experimento>")
def api_relatorio_acessivel(experimento):
    c=configuracao_experimento(experimento,request.args.get("grupo_id","").strip());return jsonify(relatorio_acessivel(experimento,c)) if c else (jsonify({"erro":"Experimento invalido"}),404)

@app.route("/grafico/<experimento>")
def grafico_experimento(experimento):
    c=configuracao_experimento(experimento,request.args.get("grupo_id","").strip())
    if not c:return "Experimento invalido",404
    caminho=_grafico_temp(analisar_experimento(experimento,c["dados"]))
    if not caminho or not os.path.exists(caminho):return "Ainda nao ha dados suficientes para gerar o grafico.",404
    return send_file(caminho,mimetype="image/png",max_age=0)

@app.route("/relatorio/<experimento>")
def gerar_pdf(experimento):
    gid=request.args.get("grupo_id","").strip();c=configuracao_experimento(experimento,gid)
    if not c:return "Experimento nao identificado.",404
    caminho=gerar_pdf_cientifico(experimento,c["dados"],grupo_id=gid)
    return send_file(caminho,as_attachment=True,download_name=f"relatorio_{experimento}.pdf")
