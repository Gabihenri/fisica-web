import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

GRAVIDADE_REFERENCIA = 9.80665


def _float(valor: Any) -> Optional[float]:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def classificar_qualidade(erro_percentual: Optional[float]) -> str:
    if erro_percentual is None:
        return "Dados insuficientes"
    if erro_percentual <= 5:
        return "Excelente"
    if erro_percentual <= 10:
        return "Boa"
    if erro_percentual <= 20:
        return "Regular"
    return "Requer revisão experimental"


def estatisticas_basicas(valores: List[float], referencia: Optional[float] = None) -> Dict[str, Any]:
    valores = [float(v) for v in valores if v is not None and math.isfinite(float(v))]
    n = len(valores)
    if not valores:
        return {
            "n": 0,
            "media": None,
            "mediana": None,
            "desvio_padrao": None,
            "erro_padrao": None,
            "coeficiente_variacao": None,
            "erro_absoluto": None,
            "erro_percentual": None,
            "qualidade": "Dados insuficientes",
            "gravidade_referencia": referencia,
            "minimo": None,
            "maximo": None,
            "amplitude": None,
        }

    media = statistics.mean(valores)
    mediana = statistics.median(valores)
    desvio = statistics.stdev(valores) if n > 1 else 0.0
    erro_padrao = desvio / math.sqrt(n) if n > 1 else 0.0
    cv = abs(desvio / media * 100) if media else None
    erro_abs = abs(media - referencia) if referencia is not None else None
    erro_pct = (erro_abs / abs(referencia) * 100) if referencia not in (None, 0) else None

    return {
        "n": n,
        "media": round(media, 5),
        "mediana": round(mediana, 5),
        "desvio_padrao": round(desvio, 5),
        "erro_padrao": round(erro_padrao, 5),
        "coeficiente_variacao": round(cv, 2) if cv is not None else None,
        "erro_absoluto": round(erro_abs, 5) if erro_abs is not None else None,
        "erro_percentual": round(erro_pct, 2) if erro_pct is not None else None,
        "qualidade": classificar_qualidade(erro_pct),
        "gravidade_referencia": referencia,
        "minimo": round(min(valores), 5),
        "maximo": round(max(valores), 5),
        "amplitude": round(max(valores) - min(valores), 5),
    }


def regressao_linear(pontos: List[Tuple[float, float]]) -> Optional[Dict[str, float]]:
    validos = [(float(x), float(y)) for x, y in pontos if math.isfinite(float(x)) and math.isfinite(float(y))]
    if len(validos) < 2:
        return None
    xs = [p[0] for p in validos]
    ys = [p[1] for p in validos]
    xm = statistics.mean(xs)
    ym = statistics.mean(ys)
    sxx = sum((x - xm) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - xm) * (y - ym) for x, y in validos)
    slope = sxy / sxx
    intercept = ym - slope * xm
    previstos = [intercept + slope * x for x in xs]
    ss_res = sum((y - yp) ** 2 for y, yp in zip(ys, previstos))
    ss_tot = sum((y - ym) ** 2 for y in ys)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return {
        "inclinação": slope,
        "intercepto": intercept,
        "r2": max(min(r2, 1.0), -1.0),
    }


def _modelo_queda(dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    pontos = []
    for d in dados:
        t = _float(d.get("tempo"))
        h = _float(d.get("altura"))
        if t is not None and h is not None:
            pontos.append((t ** 2, h))
    reg = regressao_linear(pontos)
    estimativa = 2 * reg["inclinação"] if reg else None
    return {
        "titulo_grafico": "Queda livre — altura em função de t²",
        "eixo_x": "t² (s²)",
        "eixo_y": "Altura (m)",
        "pontos": pontos,
        "regressao": reg,
        "gravidade_modelo": round(estimativa, 5) if estimativa is not None else None,
        "descricao_modelo": "No modelo ideal h = (g/2)t². A inclinação da reta permite estimar g.",
    }


def _modelo_pendulo(dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    pontos = []
    for d in dados:
        l = _float(d.get("comprimento"))
        t = _float(d.get("periodo"))
        if l is not None and t is not None:
            pontos.append((l, t ** 2))
    reg = regressao_linear(pontos)
    estimativa = (4 * math.pi ** 2 / reg["inclinação"]) if reg and reg["inclinação"] > 0 else None
    return {
        "titulo_grafico": "Pêndulo simples — T² em função do comprimento",
        "eixo_x": "Comprimento L (m)",
        "eixo_y": "T² (s²)",
        "pontos": pontos,
        "regressao": reg,
        "gravidade_modelo": round(estimativa, 5) if estimativa is not None else None,
        "descricao_modelo": "Para pequenas oscilações, T² = (4π²/g)L. A inclinação permite estimar g.",
    }


def _modelo_plano(dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    pontos = []
    for d in dados:
        ang = _float(d.get("angulo"))
        a = _float(d.get("aceleracao"))
        if a is None:
            dist = _float(d.get("distancia"))
            t = _float(d.get("tempo"))
            if dist is not None and t not in (None, 0):
                a = 2 * dist / (t ** 2)
        if ang is not None and a is not None:
            pontos.append((math.sin(math.radians(ang)), a))
    reg = regressao_linear(pontos)
    estimativa = reg["inclinação"] if reg else None
    return {
        "titulo_grafico": "Plano inclinado — aceleração em função de sen(θ)",
        "eixo_x": "sen(θ)",
        "eixo_y": "Aceleração (m/s²)",
        "pontos": pontos,
        "regressao": reg,
        "gravidade_modelo": round(estimativa, 5) if estimativa is not None else None,
        "descricao_modelo": "No plano ideal a = g·sen(θ). A inclinação da reta permite estimar g.",
    }


def analisar_experimento(chave: str, dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    valores_g = []
    for d in dados:
        g = _float(d.get("gravidade"))
        if g is not None:
            valores_g.append(g)

    stats = estatisticas_basicas(valores_g, GRAVIDADE_REFERENCIA)
    if chave == "queda":
        modelo = _modelo_queda(dados)
    elif chave == "pendulo":
        modelo = _modelo_pendulo(dados)
    elif chave == "plano":
        modelo = _modelo_plano(dados)
    else:
        modelo = {
            "titulo_grafico": "Resultados experimentais",
            "eixo_x": "Medição",
            "eixo_y": "Valor",
            "pontos": [(i + 1, v) for i, v in enumerate(valores_g)],
            "regressao": None,
            "gravidade_modelo": None,
            "descricao_modelo": "Análise descritiva das medições.",
        }

    if stats["n"] == 0:
        interpretacao = "Ainda não há medições suficientes para análise estatística."
    else:
        partes = [
            f"Foram analisadas {stats['n']} medições, com média de g = {stats['media']:.4f} m/s².",
            f"O erro percentual em relação a {GRAVIDADE_REFERENCIA:.5f} m/s² foi {stats['erro_percentual']:.2f}%.",
        ]
        if stats["n"] > 1:
            partes.append(f"O desvio padrão foi {stats['desvio_padrao']:.4f} m/s² e o coeficiente de variação foi {stats['coeficiente_variacao']:.2f}%.")
        if modelo.get("regressao"):
            partes.append(f"O ajuste linear apresentou R² = {modelo['regressao']['r2']:.4f}.")
        if modelo.get("gravidade_modelo") is not None:
            partes.append(f"A estimativa de g obtida pelo modelo gráfico foi {modelo['gravidade_modelo']:.4f} m/s².")
        partes.append(f"Classificação experimental: {stats['qualidade']}.")
        interpretacao = " ".join(partes)

    return {
        "experimento": chave,
        "estatisticas": stats,
        "modelo": modelo,
        "interpretacao": interpretacao,
    }


def estatisticas_compatibilidade(dados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Mantém o contrato já usado pelo banco de resultados."""
    return analisar_experimento("generico", dados)["estatisticas"]
