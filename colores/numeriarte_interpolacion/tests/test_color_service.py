import pytest

from app.models import ErrorColor, PuntoColor, hex_a_rgb
from app.services import (
    ColorService,
    ErrorValidacion,
    decimal_a_rgb,
    limitar_canal,
    redondear_canal,
    rgb_a_hex,
)
from conftest import TOL


@pytest.mark.parametrize("metodo", ["lagrange", "newton", "neville"])
def test_resultado_del_ejemplo(ejemplo, metodo):
    ejemplo["metodo"] = metodo
    r = ColorService().interpolar(ejemplo)
    assert r.correcto
    assert abs(r.resultado_decimal["r"] - 79.75) < TOL
    assert abs(r.resultado_decimal["g"] - 51.5) < TOL
    assert abs(r.resultado_decimal["b"] - 184.125) < TOL
    assert (r.resultado_rgb["r"], r.resultado_rgb["g"], r.resultado_rgb["b"]) == (80, 52, 184)
    assert r.hexadecimal == "#5034B8"


def test_comparacion_los_tres_coinciden(ejemplo):
    comp = ColorService().interpolar(ejemplo).comparacion
    assert comp["coinciden"]
    assert [f["metodo"] for f in comp["metodos"]] == ["Lagrange", "Newton", "Neville"]
    assert all(f["hexadecimal"] == "#5034B8" for f in comp["metodos"])
    assert all(f["diferencia_maxima"] < TOL for f in comp["metodos"])


def test_conversion_hexadecimal():
    assert hex_a_rgb("#DC143C") == (220, 20, 60)
    assert hex_a_rgb("1e90ff") == (30, 144, 255)
    assert rgb_a_hex(80, 52, 184) == "#5034B8"
    assert PuntoColor.desde_hex(3, "#800080").rgb == (128, 0, 128)


def test_redondeo_al_entero_mas_cercano():
    assert redondear_canal(79.75) == 80
    assert redondear_canal(51.5) == 52
    assert redondear_canal(184.125) == 184


def test_limitacion_entre_0_y_255():
    assert limitar_canal(-10.5) == 0
    assert limitar_canal(300) == 255
    assert limitar_canal(128) == 128
    assert decimal_a_rgb({"r": -40.2, "g": 260.7, "b": 255.4}) == {"r": 0, "g": 255, "b": 255}


def test_mural_limita_canales_fuera_de_rango(ejemplo):
    # G(x) se vuelve negativo entre 0 y 3 m con el ejemplo predeterminado.
    animacion = ColorService().interpolar(ejemplo).animacion
    assert animacion["muestras_limitadas"] > 0
    for m in animacion["muestras"]:
        assert all(0 <= m["rgb"][c] <= 255 for c in "rgb")
    limitadas = [m for m in animacion["muestras"] if m["limitado"]]
    assert any(m["decimal"]["g"] < 0 and m["rgb"]["g"] == 0 for m in limitadas)


def test_rechaza_posiciones_repetidas(ejemplo):
    ejemplo["puntos"][1]["x"] = 0
    with pytest.raises(ErrorValidacion, match="repetirse"):
        ColorService().interpolar(ejemplo)


def test_rechaza_posiciones_desordenadas(ejemplo):
    ejemplo["puntos"][0]["x"], ejemplo["puntos"][2]["x"] = 6, 0
    with pytest.raises(ErrorValidacion, match="menor a mayor"):
        ColorService().interpolar(ejemplo)


@pytest.mark.parametrize("x", [-0.1, 6.5, 100])
def test_rechaza_objetivo_fuera_del_intervalo(ejemplo, x):
    ejemplo["x_objetivo"] = x
    with pytest.raises(ErrorValidacion, match="debe quedar entre"):
        ColorService().interpolar(ejemplo)


def test_rechaza_cantidad_de_puntos(ejemplo):
    ejemplo["puntos"].pop()
    with pytest.raises(ErrorValidacion, match="exactamente tres"):
        ColorService().interpolar(ejemplo)


def test_rechaza_campos_vacios_y_no_numericos(ejemplo):
    ejemplo["puntos"][0]["x"] = ""
    ejemplo["puntos"][1]["x"] = "abc"
    with pytest.raises(ErrorValidacion) as info:
        ColorService().interpolar(ejemplo)
    assert any("vacía" in e for e in info.value.errores)
    assert any("numérica" in e for e in info.value.errores)


def test_rechaza_objetivo_vacio(ejemplo):
    ejemplo["x_objetivo"] = ""
    with pytest.raises(ErrorValidacion, match="objetivo está vacía"):
        ColorService().interpolar(ejemplo)


@pytest.mark.parametrize("color", ["#GG0000", "123", "", None, "#12345"])
def test_rechaza_colores_invalidos(ejemplo, color):
    ejemplo["puntos"][2]["color"] = color
    with pytest.raises(ErrorValidacion, match="Color 3"):
        ColorService().interpolar(ejemplo)


def test_error_color_directo():
    with pytest.raises(ErrorColor):
        PuntoColor.desde_hex(0, "rojo")


@pytest.mark.parametrize("n", [120, 242, "x"])
def test_rechaza_muestras_invalidas(ejemplo, n):
    ejemplo["muestras"] = n
    with pytest.raises(ErrorValidacion, match="muestras"):
        ColorService().interpolar(ejemplo)


def test_rechaza_metodo_desconocido(ejemplo):
    ejemplo["metodo"] = "spline"
    with pytest.raises(ErrorValidacion, match="no reconocido"):
        ColorService().interpolar(ejemplo)


@pytest.mark.parametrize("n", [121, 181, 241])
def test_muestras_equiespaciadas(ejemplo, n):
    ejemplo["muestras"] = n
    anim = ColorService().interpolar(ejemplo).animacion
    xs = [m["x"] for m in anim["muestras"]]
    assert len(xs) == n
    assert xs[0] == 0 and xs[-1] == 6
    assert anim["objetivo"]["hex"] == "#5034B8"
    assert [c["indice"] for c in anim["controles"]] == [0, (n - 1) // 2, n - 1]
