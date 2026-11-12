import pytest

from conftest import TOL


def test_pagina_principal(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "NumeriArte" in html
    assert "#5034B8" in html
    assert 'id="presentacion"' in html
    assert html.count('class="diapositiva') == 10


def test_presentacion_redirige_a_la_seccion(client):
    r = client.get("/presentacion")
    assert r.status_code == 302
    assert r.headers["Location"].endswith("/#presentacion")


def test_glosario(client):
    r = client.get("/glosario")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    for termino in ["Interpolación", "Neville", "Clamp o limitación", "Arte digital", "Nodo"]:
        assert termino in html
    assert 'id="buscador-glosario"' in html


def test_archivos_estaticos(client):
    for ruta in ["/static/css/styles.css", "/static/js/interpolacion.js",
                 "/static/js/animacion_mural.js", "/static/js/presentacion.js"]:
        assert client.get(ruta).status_code == 200, ruta


def test_404(client):
    assert client.get("/no-existe").status_code == 404


@pytest.mark.parametrize("metodo, nombre", [("lagrange", "Lagrange"), ("newton", "Newton"), ("neville", "Neville")])
def test_api_interpolar(client, ejemplo, metodo, nombre):
    ejemplo["metodo"] = metodo
    r = client.post("/api/interpolar", json=ejemplo)
    assert r.status_code == 200
    datos = r.get_json()
    assert datos["correcto"] is True
    assert datos["metodo"] == nombre
    assert datos["x_objetivo"] == 4.5
    assert abs(datos["resultado_decimal"]["r"] - 79.75) < TOL
    assert abs(datos["resultado_decimal"]["g"] - 51.5) < TOL
    assert abs(datos["resultado_decimal"]["b"] - 184.125) < TOL
    assert datos["resultado_rgb"] == {"r": 80, "g": 52, "b": 184}
    assert datos["hexadecimal"] == "#5034B8"
    assert datos["procedimiento"]["tipo"] == metodo
    assert set(datos["procedimientos"]) == {"lagrange", "newton", "neville"}
    assert len(datos["comparacion"]["metodos"]) == 3
    assert datos["tiempo_ms"] >= 0


def test_api_devuelve_muestras_del_mural(client, ejemplo):
    ejemplo["muestras"] = 241
    datos = client.post("/api/interpolar", json=ejemplo).get_json()
    muestras = datos["muestras_mural"]
    assert len(muestras) == 241
    assert muestras[0]["hex"] == "#DC143C"
    assert muestras[120]["hex"] == "#800080"
    assert muestras[-1]["hex"] == "#1E90FF"
    assert muestras[180]["hex"] == "#5034B8"  # x = 4.5 m
    assert datos["mural"]["total_muestras"] == 241
    assert "muestras" not in datos["mural"]


def test_api_error_de_validacion(client, ejemplo):
    ejemplo["x_objetivo"] = 9
    r = client.post("/api/interpolar", json=ejemplo)
    assert r.status_code == 400
    datos = r.get_json()
    assert datos["correcto"] is False
    assert "debe quedar entre" in datos["mensaje"]


def test_api_rechaza_cuerpo_no_json(client):
    r = client.post("/api/interpolar", data="hola", content_type="text/plain")
    assert r.status_code == 400
    assert r.get_json()["correcto"] is False


def test_api_get_no_permitido(client):
    r = client.get("/api/interpolar")
    assert r.status_code == 405
    assert r.get_json()["correcto"] is False
