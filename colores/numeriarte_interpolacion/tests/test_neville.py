import pytest

from app.metodos_numericos import ErrorInterpolacion, InterpoladorNeville
from app.models import PuntoColor
from conftest import TOL, verificar_ejemplo, verificar_nodos


def test_reproduce_nodos(puntos):
    verificar_nodos(InterpoladorNeville(), puntos)


def test_ejemplo_x_4_5(puntos):
    verificar_ejemplo(InterpoladorNeville(), puntos)


@pytest.mark.parametrize("canal, p01, p12, p02", [
    ("r", 82.0, 79.0, 79.75),
    ("g", -10.0, 72.0, 51.5),
    ("b", 162.0, 191.5, 184.125),
])
def test_tabla_triangular(puntos, canal, p01, p12, p02):
    niveles = InterpoladorNeville().resolver(puntos, 4.5)["procedimiento"]["canales"][canal]["niveles"]
    assert len(niveles) == 3
    assert [n["valor"] for n in niveles[1]] == pytest.approx([p01, p12], abs=TOL)
    assert niveles[2][0]["valor"] == pytest.approx(p02, abs=TOL)
    assert (niveles[2][0]["i"], niveles[2][0]["j"]) == (0, 2)


def test_rechaza_posiciones_repetidas():
    repetidos = [PuntoColor.desde_hex(2, "#000000"), PuntoColor.desde_hex(3, "#FFFFFF"),
                 PuntoColor.desde_hex(2, "#FF0000")]
    with pytest.raises(ErrorInterpolacion):
        InterpoladorNeville().resolver(repetidos, 2.5)
