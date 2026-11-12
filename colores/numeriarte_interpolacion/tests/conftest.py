import copy

import pytest

from app import create_app
from app.models import PuntoColor
from app.services import EJEMPLO_PREDETERMINADO

TOL = 1e-9
ESPERADO_45 = {"r": 79.75, "g": 51.5, "b": 184.125}


@pytest.fixture
def puntos():
    return [
        PuntoColor.desde_hex(0, "#DC143C", "Carmesí"),
        PuntoColor.desde_hex(3, "#800080", "Morado"),
        PuntoColor.desde_hex(6, "#1E90FF", "Azul"),
    ]


@pytest.fixture
def ejemplo():
    return copy.deepcopy(EJEMPLO_PREDETERMINADO)


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def verificar_nodos(interpolador, puntos):
    for p in puntos:
        valores = interpolador.evaluar(puntos, p.x)
        assert abs(valores["r"] - p.r) < TOL
        assert abs(valores["g"] - p.g) < TOL
        assert abs(valores["b"] - p.b) < TOL


def verificar_ejemplo(interpolador, puntos):
    valores = interpolador.resolver(puntos, 4.5)["valores"]
    for canal, esperado in ESPERADO_45.items():
        assert abs(valores[canal] - esperado) < TOL, canal
    assert f"{valores['r']:.5f}" == "79.75000"
    assert f"{valores['g']:.5f}" == "51.50000"
    assert f"{valores['b']:.5f}" == "184.12500"
