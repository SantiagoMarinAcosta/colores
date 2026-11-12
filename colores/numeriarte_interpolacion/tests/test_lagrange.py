import pytest

from app.metodos_numericos import ErrorInterpolacion, InterpoladorLagrange
from app.models import PuntoColor
from conftest import TOL, verificar_ejemplo, verificar_nodos


def test_reproduce_nodos(puntos):
    verificar_nodos(InterpoladorLagrange(), puntos)


def test_ejemplo_x_4_5(puntos):
    verificar_ejemplo(InterpoladorLagrange(), puntos)


def test_bases_de_lagrange(puntos):
    proc = InterpoladorLagrange().resolver(puntos, 4.5)["procedimiento"]
    valores = [b["valor"] for b in proc["bases"]]
    assert valores == pytest.approx([-0.125, 0.75, 0.375], abs=TOL)
    assert abs(proc["suma_bases"] - 1.0) < TOL
    # L0 = (4.5-3)(4.5-6) / ((0-3)(0-6))
    assert proc["bases"][0]["numerador"] == pytest.approx(1.5 * -1.5)
    assert proc["bases"][0]["denominador"] == pytest.approx(18.0)


def test_terminos_canal_rojo(puntos):
    proc = InterpoladorLagrange().resolver(puntos, 4.5)["procedimiento"]
    productos = [t["producto"] for t in proc["canales"]["r"]["terminos"]]
    assert productos == pytest.approx([220 * -0.125, 128 * 0.75, 30 * 0.375], abs=TOL)


def test_rechaza_posiciones_repetidas():
    repetidos = [PuntoColor.desde_hex(0, "#000000"), PuntoColor.desde_hex(0, "#FFFFFF"),
                 PuntoColor.desde_hex(6, "#FF0000")]
    with pytest.raises(ErrorInterpolacion):
        InterpoladorLagrange().resolver(repetidos, 3)
