from flask import render_template

from app_core import app


@app.route("/laboratorio-sensores")
def laboratorio_sensores():
    return render_template("laboratorio_sensores.html")


if __name__ == "__main__":
    app.run(debug=True)
