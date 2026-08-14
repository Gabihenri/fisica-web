from flask import render_template

from app_core import app


@app.route("/acesso")
def acesso():
    return render_template("acesso.html")


@app.route("/laboratorio-movel")
def laboratorio_movel():
    return render_template("laboratorio_movel.html")


@app.route("/laboratorio-sensores")
def laboratorio_sensores():
    return render_template("laboratorio_sensores.html")


@app.route("/laboratorio-elevador")
def laboratorio_elevador():
    return render_template("laboratorio_elevador.html")


@app.route("/laboratorio-pendulo")
def laboratorio_pendulo():
    return app.send_static_file("laboratorio-pendulo.html")


@app.route("/laboratorio-plano-inclinado")
def laboratorio_plano_inclinado():
    return render_template("laboratorio_plano_inclinado.html")


@app.route("/laboratorio-som")
def laboratorio_som():
    return render_template("laboratorio_som.html")


if __name__ == "__main__":
    app.run(debug=True)
