"""Fábrica de la aplicación NumeriArte."""
from flask import Flask, jsonify, render_template, request

from config import obtener_configuracion


def formato_cinco(valor) -> str:
    """Filtro Jinja: número con cinco decimales (evita mostrar -0.00000)."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor)
    if abs(numero) < 5e-6:
        numero = 0.0
    return f"{numero:.5f}"


def formato_metros(valor) -> str:
    return f"{float(valor):g}"


def create_app(nombre_config=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(obtener_configuracion(nombre_config))
    app.json.sort_keys = False
    app.json.ensure_ascii = False

    app.add_template_filter(formato_cinco, "f5")
    app.add_template_filter(formato_metros, "m")

    from .controllers import glosario_bp, interpolacion_bp

    app.register_blueprint(interpolacion_bp)
    app.register_blueprint(glosario_bp)

    @app.errorhandler(404)
    def no_encontrado(_error):
        if request.path.startswith("/api/"):
            return jsonify(correcto=False, mensaje="Recurso no encontrado."), 404
        return render_template("error.html", codigo=404, mensaje="La página solicitada no existe."), 404

    @app.errorhandler(405)
    def metodo_no_permitido(_error):
        if request.path.startswith("/api/"):
            return jsonify(correcto=False, mensaje="Use el método POST con un cuerpo JSON."), 405
        return render_template("error.html", codigo=405, mensaje="Método no permitido."), 405

    return app
