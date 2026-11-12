"""Servicio de interpolación cromática.

Orquesta: validación de entradas → construcción de PuntoColor → métodos
numéricos → conversión a color → comparación → muestras del mural.
Aquí no hay fórmulas de interpolación: estas viven en app/metodos_numericos.
"""
from __future__ import annotations

import math
import time

from app.metodos_numericos import CANALES, METODOS, ErrorInterpolacion, obtener_interpolador
from app.models import ErrorColor, PuntoColor, ResultadoInterpolacion

MUESTRAS_MIN = 121
MUESTRAS_MAX = 241
TOLERANCIA_COINCIDENCIA = 1e-9
NOMBRES_CANAL = {"r": "R (rojo)", "g": "G (verde)", "b": "B (azul)"}

NOMBRES_CONOCIDOS = {"#DC143C": "Carmesí", "#800080": "Morado", "#1E90FF": "Azul"}

EJEMPLO_PREDETERMINADO = {
    "puntos": [
        {"x": 0, "color": "#DC143C", "nombre": "Carmesí"},
        {"x": 3, "color": "#800080", "nombre": "Morado"},
        {"x": 6, "color": "#1E90FF", "nombre": "Azul"},
    ],
    "x_objetivo": 4.5,
    "metodo": "lagrange",
    "muestras": MUESTRAS_MIN,
}

EXPLICACION_COMPARACION = (
    "Los tres métodos producen el mismo resultado porque construyen el mismo "
    "polinomio interpolador con los mismos puntos. Lo que cambia es el "
    "procedimiento de cálculo."
)


class ErrorValidacion(ValueError):
    """Agrupa uno o varios mensajes de validación comprensibles."""

    def __init__(self, errores):
        self.errores = [errores] if isinstance(errores, str) else list(errores)
        super().__init__(" ".join(self.errores))


# --------------------------------------------------------------------------
# Conversión de valores decimales a color
# --------------------------------------------------------------------------
def redondear_canal(valor: float) -> int:
    """Entero más cercano (los empates .5 se redondean hacia arriba)."""
    if not math.isfinite(valor):
        raise ErrorValidacion("El cálculo produjo un valor no finito en un canal de color.")
    return math.floor(valor + 0.5)


def limitar_canal(valor, minimo: int = 0, maximo: int = 255):
    """Clamp: limita el valor al intervalo [minimo, maximo]."""
    return max(minimo, min(maximo, valor))


def decimal_a_rgb(valores: dict) -> dict:
    """1) redondea, 2) limita a [0, 255]."""
    return {c: limitar_canal(redondear_canal(valores[c])) for c in CANALES}


def rgb_a_hex(r: int, g: int, b: int) -> str:
    """3) convierte la terna entera a '#RRGGBB'."""
    for nombre, v in (("R", r), ("G", g), ("B", b)):
        if not isinstance(v, int) or not 0 <= v <= 255:
            raise ErrorValidacion(f"El canal {nombre}={v!r} debe ser un entero entre 0 y 255.")
    return f"#{r:02X}{g:02X}{b:02X}"


def canales_fuera_de_rango(valores: dict) -> list[str]:
    """Canales cuyo valor redondeado quedó fuera de [0, 255] y fue limitado."""
    return [c for c in CANALES if not 0 <= redondear_canal(valores[c]) <= 255]


# --------------------------------------------------------------------------
# Servicio
# --------------------------------------------------------------------------
class ColorService:
    def __init__(self, muestras_defecto: int = MUESTRAS_MIN):
        self.muestras_defecto = muestras_defecto

    # ---------------- validación ----------------
    @staticmethod
    def _leer_numero(valor, etiqueta: str, errores: list):
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            errores.append(f"{etiqueta} está vacía.")
            return None
        if isinstance(valor, bool):
            errores.append(f"{etiqueta} debe ser un número.")
            return None
        if isinstance(valor, str):
            valor = valor.strip().replace(",", ".")
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            errores.append(f"{etiqueta} debe ser numérica (se recibió «{valor}»).")
            return None
        if not math.isfinite(numero):
            errores.append(f"{etiqueta} debe ser un número finito.")
            return None
        return numero

    def construir_puntos(self, datos_puntos) -> list[PuntoColor]:
        """Valida la lista de puntos y la convierte en PuntoColor."""
        if not isinstance(datos_puntos, list):
            raise ErrorValidacion("Debe enviarse una lista con los tres puntos de control.")
        if len(datos_puntos) != 3:
            raise ErrorValidacion(
                f"Deben existir exactamente tres puntos de control; se recibieron {len(datos_puntos)}."
            )
        errores, puntos = [], []
        for i, dato in enumerate(datos_puntos):
            if not isinstance(dato, dict):
                errores.append(f"El punto {i + 1} no tiene el formato esperado.")
                continue
            x = self._leer_numero(dato.get("x"), f"La posición del color {i + 1}", errores)
            try:
                color = dato.get("color")
                nombre = str(dato.get("nombre") or "").strip()[:30]
                if x is not None:
                    hexa = PuntoColor.desde_hex(x, color).hexadecimal
                    puntos.append(PuntoColor.desde_hex(
                        x, color, nombre or NOMBRES_CONOCIDOS.get(hexa, f"Color {i + 1}")))
                else:
                    PuntoColor.desde_hex(0, color)  # valida también el color
            except ErrorColor as exc:
                errores.append(f"Color {i + 1}: {exc}")
        if errores:
            raise ErrorValidacion(errores)

        xs = [p.x for p in puntos]
        if len(set(xs)) != len(xs):
            raise ErrorValidacion(
                "Las posiciones no pueden repetirse: dos colores en el mismo lugar "
                "harían cero un denominador (x_i − x_j)."
            )
        if any(xs[i] >= xs[i + 1] for i in range(len(xs) - 1)):
            raise ErrorValidacion(
                "Las posiciones deben ingresarse de menor a mayor (x₀ < x₁ < x₂)."
            )
        return puntos

    def validar_objetivo(self, valor, puntos: list[PuntoColor]) -> float:
        errores = []
        x = self._leer_numero(valor, "La posición objetivo", errores)
        if errores:
            raise ErrorValidacion(errores)
        a, b = puntos[0].x, puntos[-1].x
        if not a <= x <= b:
            raise ErrorValidacion(
                f"La posición objetivo ({x:g} m) debe quedar entre {a:g} m y {b:g} m; "
                "fuera de ese intervalo sería extrapolación."
            )
        return x

    def validar_muestras(self, valor) -> int:
        if valor is None or valor == "":
            return self.muestras_defecto
        try:
            n = int(valor)
        except (TypeError, ValueError):
            raise ErrorValidacion("El número de muestras debe ser un entero.") from None
        if isinstance(valor, bool) or float(valor) != n or not MUESTRAS_MIN <= n <= MUESTRAS_MAX:
            raise ErrorValidacion(
                f"El número de muestras del mural debe ser un entero entre {MUESTRAS_MIN} y {MUESTRAS_MAX}."
            )
        return n

    # ---------------- cálculo ----------------
    def interpolar(self, datos: dict) -> ResultadoInterpolacion:
        """Caso de uso completo que consume el controlador."""
        if not isinstance(datos, dict):
            raise ErrorValidacion("La solicitud debe ser un objeto JSON.")
        inicio = time.perf_counter()
        puntos = self.construir_puntos(datos.get("puntos"))
        x_obj = self.validar_objetivo(datos.get("x_objetivo"), puntos)
        n = self.validar_muestras(datos.get("muestras"))
        try:
            seleccionado = obtener_interpolador(datos.get("metodo") or "lagrange")
            resultados = {clave: cls().resolver(puntos, x_obj) for clave, cls in METODOS.items()}
            animacion = self.generar_muestras_mural(seleccionado, puntos, x_obj, n)
        except ErrorInterpolacion as exc:
            raise ErrorValidacion(str(exc)) from exc

        principal = resultados[seleccionado.clave]
        decimal = principal["valores"]
        rgb = decimal_a_rgb(decimal)
        hexadecimal = rgb_a_hex(rgb["r"], rgb["g"], rgb["b"])
        limitados = canales_fuera_de_rango(decimal)
        comparacion = self.comparar(resultados)

        mensaje = f"Cálculo correcto con {seleccionado.nombre} en x = {x_obj:g} m."
        if comparacion["coinciden"]:
            mensaje += " Lagrange, Newton y Neville coinciden."
        if limitados:
            detalles = ", ".join(f"{NOMBRES_CANAL[c]} = {decimal[c]:.5f}" for c in limitados)
            mensaje += f" Atención: {detalles} quedó fuera de [0, 255] y se limitó."

        return ResultadoInterpolacion(
            metodo=seleccionado.nombre,
            clave_metodo=seleccionado.clave,
            x_objetivo=x_obj,
            resultado_decimal=dict(decimal),
            resultado_rgb=rgb,
            hexadecimal=hexadecimal,
            procedimiento=principal["procedimiento"],
            procedimientos={c: r["procedimiento"] for c, r in resultados.items()},
            comparacion=comparacion,
            mensaje=mensaje,
            correcto=True,
            animacion=animacion,
            puntos=[p.to_dict() for p in puntos],
            canales_limitados=limitados,
            tiempo_ms=(time.perf_counter() - inicio) * 1000.0,
        )

    @staticmethod
    def comparar(resultados: dict) -> dict:
        referencia = resultados["lagrange"]["valores"]
        filas, max_global = [], 0.0
        for clave, res in resultados.items():
            valores = res["valores"]
            rgb = decimal_a_rgb(valores)
            diferencia = max(abs(valores[c] - referencia[c]) for c in CANALES)
            max_global = max(max_global, diferencia)
            filas.append({
                "clave": clave,
                "metodo": res["metodo"],
                "decimal": dict(valores),
                "rgb": rgb,
                "hexadecimal": rgb_a_hex(rgb["r"], rgb["g"], rgb["b"]),
                "diferencia_maxima": diferencia,
                "tiempo_ms": res["tiempo_ms"],
            })
        return {
            "referencia": "Lagrange",
            "metodos": filas,
            "diferencia_maxima_global": max_global,
            "coinciden": max_global < TOLERANCIA_COINCIDENCIA,
            "explicacion": EXPLICACION_COMPARACION,
        }

    @staticmethod
    def generar_muestras_mural(interpolador, puntos, x_objetivo: float, n: int) -> dict:
        """Evalúa el método seleccionado en n posiciones equiespaciadas del mural."""
        a, b = puntos[0].x, puntos[-1].x
        paso = (b - a) / (n - 1)
        muestras, limitadas = [], 0
        for k in range(n):
            x = b if k == n - 1 else a + k * paso
            valores = interpolador.evaluar(puntos, x)
            rgb = decimal_a_rgb(valores)
            fuera = bool(canales_fuera_de_rango(valores))
            limitadas += fuera
            muestras.append({
                "indice": k,
                "x": x,
                "decimal": dict(valores),
                "rgb": rgb,
                "hex": rgb_a_hex(rgb["r"], rgb["g"], rgb["b"]),
                "limitado": fuera,
            })

        def indice_cercano(x):
            return min(range(n), key=lambda k: abs(muestras[k]["x"] - x))

        valores_obj = interpolador.evaluar(puntos, x_objetivo)
        rgb_obj = decimal_a_rgb(valores_obj)
        return {
            "metodo": interpolador.nombre,
            "x_min": a,
            "x_max": b,
            "total_muestras": n,
            "muestras_limitadas": limitadas,
            "controles": [
                {"x": p.x, "hex": p.hexadecimal, "nombre": p.nombre,
                 "rgb": {"r": p.r, "g": p.g, "b": p.b}, "indice": indice_cercano(p.x)}
                for p in puntos
            ],
            "objetivo": {
                "x": x_objetivo, "rgb": rgb_obj,
                "hex": rgb_a_hex(rgb_obj["r"], rgb_obj["g"], rgb_obj["b"]),
                "indice": indice_cercano(x_objetivo),
            },
            "muestras": muestras,
        }
