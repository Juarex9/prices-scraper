import asyncio
from threading import Thread
from flask import Flask, render_template, request
from web_scrp import orquestador_de_busqueda

app = Flask(__name__)

cache = {}


def buscar_en_thread(termino):
    resultados_raw = asyncio.run(orquestador_de_busqueda(termino))
    resultados = []
    for item in resultados_raw:
        resultados.append({
            "supermercado_id": item.get("supermercado", "Unknown"),
            "titulo_encontrado": item.get("producto_encontrado", ""),
            "precio": item.get("precio", 0),
            "url_compra": item.get("url", ""),
            "precio_x_unidad": item.get("precio_x_unidad", "No informado"),
        })
    cache[termino] = resultados
    return resultados


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/buscar")
def buscar():
    termino = request.args.get("termino", "").strip().lower()

    if len(termino) < 2:
        return render_template("resultados.html", termino=termino, resultados=[], error="Mínimo 2 caracteres")

    if termino in cache:
        return render_template("resultados.html", termino=termino, resultados=cache[termino])

    resultados = buscar_en_thread(termino)
    return render_template("resultados.html", termino=termino, resultados=resultados)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
