import pytest

from app.metodos_numericos import ErrorInterpolacion, InterpoladorNewton
from app.models import PuntoColor
from conftest import TOL, verificar_ejemplo, verificar_nodos


def test_reproduce_nodos(puntos):
    verificar_nodos(InterpoladorNewton(), puntos)


def test_ejemplo_x_4_5(puntos):
    verificar_ejemplo(InterpoladorNewton(), puntos)


@pytest.mark.parametrize("canal, primeras, segunda", [
    ("r", [-92 / 3, -98 / 3], -1 / 3),
    ("g", [-20 / 3, 48.0], 82 / 9),
    ("b", [68 / 3, 127 / 3], 59 / 18),
])
def test_tabla_de_diferencias(puntos, canal, primeras, segunda):
    proc = InterpoladorNewton().resolver(puntos, 4.5)["procedimiento"]["canales"][canal]
    assert proc["columnas"][1] == pytest.approx(primeras, abs=TOL)
    assert proc["columnas"][2][0] == pytest.approx(segunda, abs=TOL)
    assert proc["coeficientes"][0] == proc["valores_y"][0]


def test_valores_redondeados_del_enunciado(puntos):
    canales = InterpoladorNewton().resolver(puntos, 4.5)["procedimiento"]["canales"]
    assert f"{canales['g']['columnas'][2][0]:.5f}" == "9.11111"
    assert f"{canales['b']['columnas'][2][0]:.5f}" == "3.27778"
    assert f"{canales['r']['columnas'][1][0]:.5f}" == "-30.66667"


def test_rechaza_posiciones_repetidas():
    repetidos = [PuntoColor.desde_hex(0, "#000000"), PuntoColor.desde_hex(3, "#FFFFFF"),
                 PuntoColor.desde_hex(3, "#FF0000")]
    with pytest.raises(ErrorInterpolacion):
        InterpoladorNewton().resolver(repetidos, 1)
