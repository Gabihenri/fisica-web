"""Helper para registrar o catálogo público na aplicação Flask."""


def registrar_catalogo(app):
    from catalogo_publico import registrar_catalogo_publico
    registrar_catalogo_publico(app)
