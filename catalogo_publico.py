from flask import render_template, abort

from experimentos_catalogo import listar_experimentos_novos


def registrar_catalogo_publico(app):
    """Registra o catálogo sem envolver o security_guard de dados escolares."""

    @app.get("/experimentos")
    def catalogo_experimentos_publico():
        return render_template("experimentos.html", experimentos=listar_experimentos_novos())

    @app.get("/experimentos/<slug>")
    def detalhe_experimento_publico(slug):
        experimento = next((e for e in listar_experimentos_novos() if e["slug"] == slug), None)
        if experimento is None:
            abort(404)
        return render_template("experimento_detalhe.html", experimento=experimento)
