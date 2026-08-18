import io
import os
import tempfile
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF

from scientific_engine import GRAVIDADE_REFERENCIA, analisar_experimento


SUBSTITUICOES = {
    "²": "2", "³": "3", "π": "pi", "θ": "theta", "±": "+/-", "→": "->",
    "·": "*", "–": "-", "—": "-", "“": '"', "”": '"', "’": "'",
}

GRAFICO_AZUL_ESCURO = "#0A3158"


def texto_pdf(valor: Any) -> str:
    texto = str(valor if valor is not None else "")
    for origem, destino in SUBSTITUICOES.items():
        texto = texto.replace(origem, destino)
    return texto.encode("latin-1", "replace").decode("latin-1")


def _fmt_num(valor: Any, casas: int = 5, sufixo: str = "") -> str:
    try:
        if valor is None:
            return "-"
        return f"{float(valor):.{casas}f}{sufixo}"
    except (TypeError, ValueError):
        return texto_pdf(valor)


def _grafico_temp(analise: Dict[str, Any]) -> Optional[str]:
    """Gera o gráfico sem impedir o PDF caso o ambiente gráfico falhe."""
    try:
        modelo = analise.get("modelo") or {}
        pontos = modelo.get("pontos") or []
        if not pontos:
            return None

        xs = [float(p[0]) for p in pontos]
        ys = [float(p[1]) for p in pontos]
        arquivo = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        caminho = arquivo.name
        arquivo.close()

        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        ax.scatter(xs, ys, s=48, color=GRAFICO_AZUL_ESCURO, label="Dados experimentais")

        reg = modelo.get("regressao")
        if reg and len(xs) >= 2:
            minimo, maximo = min(xs), max(xs)
            margem = (maximo - minimo) * 0.05 if maximo != minimo else 0.1
            linha_x = [minimo - margem, maximo + margem]
            inclinacao = float(reg.get("inclinação", 0) or 0)
            intercepto = float(reg.get("intercepto", 0) or 0)
            linha_y = [intercepto + inclinacao * x for x in linha_x]
            ax.plot(
                linha_x,
                linha_y,
                color=GRAFICO_AZUL_ESCURO,
                linewidth=2,
                label=f"Ajuste linear (R2={float(reg.get('r2', 0) or 0):.4f})",
            )

        ax.set_title(
            modelo.get("titulo_grafico") or "Resultados experimentais",
            fontweight="bold",
            color=GRAFICO_AZUL_ESCURO,
        )
        ax.set_xlabel(modelo.get("eixo_x") or "x", color=GRAFICO_AZUL_ESCURO)
        ax.set_ylabel(modelo.get("eixo_y") or "y", color=GRAFICO_AZUL_ESCURO)
        ax.tick_params(axis="both", colors=GRAFICO_AZUL_ESCURO)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="best", fontsize=9)
        fig.tight_layout()
        fig.savefig(caminho, dpi=160, bbox_inches="tight", format="png")
        plt.close(fig)
        return caminho
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _titulo(pdf: FPDF, titulo: str, subtitulo: str) -> None:
    pdf.set_fill_color(10, 49, 88)
    pdf.rect(0, 0, 210, 34, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(12, 7)
    pdf.set_font("Arial", "B", 17)
    pdf.cell(0, 8, texto_pdf(titulo), ln=True)
    pdf.set_x(12)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, texto_pdf(subtitulo), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(40)


def _secao(pdf: FPDF, numero: int, titulo: str) -> None:
    if pdf.get_y() > 255:
        pdf.add_page()
    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(10, 49, 88)
    pdf.cell(0, 8, texto_pdf(f"{numero}. {titulo}"), ln=True)
    pdf.set_text_color(0, 0, 0)


def _linha_identificacao(pdf: FPDF, rotulo: str, valor: Any) -> None:
    if valor in (None, ""):
        return
    pdf.set_font("Arial", "B", 9)
    pdf.cell(38, 6, texto_pdf(rotulo), 0, 0)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 6, texto_pdf(valor))


def _tabela_dados(pdf: FPDF, dados: List[Dict[str, Any]]) -> None:
    if not dados:
        pdf.set_font("Arial", "", 9)
        pdf.multi_cell(0, 6, "Nenhuma medicao registrada.")
        return

    colunas = list(dados[0].keys())
    if not colunas:
        pdf.multi_cell(0, 6, "Nenhuma medicao registrada.")
        return
    largura_util = 186
    largura = max(min(largura_util / max(len(colunas), 1), 48), 24)

    pdf.set_font("Arial", "B", 7.5)
    pdf.set_fill_color(237, 244, 251)
    for coluna in colunas:
        pdf.cell(largura, 7, texto_pdf(coluna.replace("_", " ").title())[:22], 1, 0, "C", True)
    pdf.ln()

    pdf.set_font("Arial", "", 7.5)
    for linha in dados:
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font("Arial", "B", 7.5)
            for coluna in colunas:
                pdf.cell(largura, 7, texto_pdf(coluna.replace("_", " ").title())[:22], 1, 0, "C", True)
            pdf.ln()
            pdf.set_font("Arial", "", 7.5)
        for coluna in colunas:
            valor = linha.get(coluna, "")
            if isinstance(valor, float):
                valor = f"{valor:.5g}"
            pdf.cell(largura, 7, texto_pdf(valor)[:22], 1, 0, "C")
        pdf.ln()


def gerar_pdf_cientifico(chave: str, titulo_experimento: str, teoria: str, dados: List[Dict[str, Any]], contexto: Optional[Dict[str, Any]] = None) -> io.BytesIO:
    dados = dados or []
    analise = analisar_experimento(chave, dados)
    stats = analise.get("estatisticas") or {}
    modelo = analise.get("modelo") or {}
    caminho_grafico = _grafico_temp(analise)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    _titulo(pdf, "Fisica Web", f"Relatorio Cientifico Experimental - {titulo_experimento}")

    grupo = (contexto or {}).get("grupo") or {}
    turma = (contexto or {}).get("turma") or {}
    escola = (contexto or {}).get("escola") or {}
    participantes = (contexto or {}).get("participantes") or []

    _secao(pdf, 1, "Identificacao")
    _linha_identificacao(pdf, "Escola:", escola.get("nome"))
    serie_turma = f"{turma.get('serie_ano', '')} - {turma.get('turma', '')}".strip(" -")
    _linha_identificacao(pdf, "Serie/Turma:", serie_turma)
    _linha_identificacao(pdf, "Grupo:", grupo.get("codigo_grupo"))
    nomes = [p.get("nome_exibicao", "") for p in participantes if isinstance(p, dict) and p.get("nome_exibicao")]
    if nomes:
        _linha_identificacao(pdf, "Participantes:", ", ".join(nomes))

    _secao(pdf, 2, "Objetivo e referencial teorico")
    pdf.set_font("Arial", "", 9.5)
    pdf.multi_cell(0, 6, texto_pdf(teoria))

    _secao(pdf, 3, "Dados experimentais")
    _tabela_dados(pdf, dados)

    _secao(pdf, 4, "Tratamento estatistico")
    pdf.set_font("Arial", "", 9.5)
    n = int(stats.get("n") or 0)
    if n == 0:
        pdf.multi_cell(0, 6, "Ainda nao ha dados suficientes para analise estatistica.")
    else:
        indicadores = [
            ("Numero de medicoes", n),
            ("Media de g", _fmt_num(stats.get("media"), 5, " m/s2")),
            ("Mediana de g", _fmt_num(stats.get("mediana"), 5, " m/s2")),
            ("Desvio padrao", _fmt_num(stats.get("desvio_padrao"), 5, " m/s2")),
            ("Erro padrao", _fmt_num(stats.get("erro_padrao"), 5, " m/s2")),
            ("Minimo / Maximo", f"{_fmt_num(stats.get('minimo'),5)} / {_fmt_num(stats.get('maximo'),5)} m/s2"),
            ("Valor de referencia", f"{GRAVIDADE_REFERENCIA:.5f} m/s2"),
            ("Erro percentual", _fmt_num(stats.get("erro_percentual"), 2, "%")),
            ("Coeficiente de variacao", _fmt_num(stats.get("coeficiente_variacao"), 2, "%")),
            ("Classificacao", stats.get("qualidade") or "-"),
        ]
        for rotulo, valor in indicadores:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(63, 7, texto_pdf(rotulo), 1)
            pdf.set_font("Arial", "", 9)
            pdf.cell(123, 7, texto_pdf(valor), 1, 1)

    _secao(pdf, 5, "Modelo fisico e grafico")
    pdf.set_font("Arial", "", 9.5)
    pdf.multi_cell(0, 6, texto_pdf(modelo.get("descricao_modelo") or "Analise grafica indisponivel para esta medicao."))
    reg = modelo.get("regressao")
    if reg:
        pdf.multi_cell(0, 6, texto_pdf(
            f"Ajuste linear: inclinacao = {float(reg.get('inclinação',0) or 0):.6g}; "
            f"intercepto = {float(reg.get('intercepto',0) or 0):.6g}; R2 = {float(reg.get('r2',0) or 0):.5f}."
        ))
    if modelo.get("gravidade_modelo") is not None:
        pdf.multi_cell(0, 6, texto_pdf(f"Estimativa de g pelo modelo grafico: {_fmt_num(modelo.get('gravidade_modelo'),5)} m/s2."))
    if caminho_grafico and os.path.exists(caminho_grafico):
        try:
            if pdf.get_y() > 165:
                pdf.add_page()
            pdf.ln(3)
            pdf.image(caminho_grafico, x=15, w=180)
        except Exception:
            pdf.ln(2)
            pdf.set_font("Arial", "I", 8.5)
            pdf.multi_cell(0, 5, "Grafico nao incorporado ao PDF. Os dados e a analise textual permanecem validos.")

    _secao(pdf, 6, "Discussao e interpretacao")
    pdf.set_font("Arial", "", 9.5)
    pdf.multi_cell(0, 6, texto_pdf(analise.get("interpretacao") or "Sem interpretacao disponivel."))

    _secao(pdf, 7, "Conclusao e acessibilidade")
    pdf.set_font("Arial", "", 9.5)
    if n:
        conclusao = (
            f"O experimento apresentou media de g igual a {_fmt_num(stats.get('media'),4)} m/s2, "
            f"com erro percentual de {_fmt_num(stats.get('erro_percentual'),2)}% em relacao ao valor de referencia. "
            f"A qualidade foi classificada como {stats.get('qualidade') or 'nao classificada'}."
        )
    else:
        conclusao = "Nao ha dados suficientes para elaborar uma conclusao experimental."
    pdf.multi_cell(0, 6, texto_pdf(conclusao))
    pdf.ln(2)
    pdf.set_font("Arial", "I", 8.5)
    pdf.multi_cell(0, 5, texto_pdf("Este relatorio possui equivalente textual para os principais resultados e deve ser acompanhado pela audiodescricao disponivel na interface do Fisica Web."))

    conteudo = pdf.output(dest="S")
    if isinstance(conteudo, str):
        conteudo = conteudo.encode("latin-1", "replace")
    elif isinstance(conteudo, bytearray):
        conteudo = bytes(conteudo)
    elif not isinstance(conteudo, bytes):
        conteudo = bytes(conteudo)

    buffer = io.BytesIO(conteudo)
    buffer.seek(0)

    if caminho_grafico and os.path.exists(caminho_grafico):
        try:
            os.remove(caminho_grafico)
        except OSError:
            pass
    return buffer
