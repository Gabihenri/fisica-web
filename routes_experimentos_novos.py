"""Rotas públicas do catálogo inicial de novos experimentos."""

from flask import Blueprint, render_template, abort

from experimentos_catalogo import listar_experimentos_novos

bp_experimentos_novos = Blueprint("experimentos_novos", __name__)


@bp_experimentos_novos.get("/experimentos")
def catalogo_experimentos():
    return render_template("experimentos.html", experimentos=listar_experimentos_novos())


@bp_experimentos_novos.get("/experimentos/<slug>")
def detalhe_experimento(slug):
    experimento = next((e for e in listar_experimentos_novos() if e["slug"] == slug), None)
    if experimento is None:
        abort(404)
    return render_template("experimento_detalhe.html", experimento=experimento)
