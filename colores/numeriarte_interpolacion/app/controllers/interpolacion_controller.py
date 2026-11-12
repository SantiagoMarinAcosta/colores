"""Controlador de la interpolación cromática.

Solo valida la forma de la solicitud, delega en ColorService y entrega el
resultado a la vista (HTML) o como JSON. No contiene fórmulas.
"""
import copy

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from app.services import EJEMPLO_PREDETERMINADO, ColorService, ErrorValidacion

bp = Blueprint("interpolacion", __name__)


def _servicio() -> ColorService:
    return ColorService(current_app.config.get("MUESTRAS_MURAL_DEFECTO", 121))


@bp.get("/")
def index():
    ejemplo = _servicio().interpolar(copy.deepcopy(EJEMPLO_PREDETERMINADO)).to_dict()
    return render_template(
        "interpolacion.html",
        ejemplo=ejemplo,
        entrada=EJEMPLO_PREDETERMINADO,
        pagina="interpolacion",
    )


@bp.get("/presentacion")
def presentacion():
    """La presentación está integrada en la página principal."""
    return redirect(url_for("interpolacion.index") + "#presentacion")


@bp.post("/api/interpolar")
def api_interpolar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify(correcto=False, mensaje="La solicitud debe contener un objeto JSON válido.",
                       errores=["La solicitud debe contener un objeto JSON válido."]), 400
    try:
        resultado = _servicio().interpolar(datos)
    except ErrorValidacion as exc:
        return jsonify(correcto=False, mensaje=" ".join(exc.errores), errores=exc.errores), 400
    return jsonify(resultado.to_dict())
