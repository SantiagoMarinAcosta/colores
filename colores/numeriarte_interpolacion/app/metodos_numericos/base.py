"""Clase base de los interpoladores cromáticos.

Cada canal (R, G, B) se interpola de forma independiente con los mismos nodos x.
Los cálculos se hacen en punto flotante de doble precisión SIN redondeos
intermedios; el redondeo a cinco decimales ocurre solo al presentar resultados.
"""
from __future__ import annotations

import math
import time
from abc import ABC, abstractmethod

CANALES = ("r", "g", "b")


class ErrorInterpolacion(ValueError):
    """Datos que impiden construir el polinomio interpolador."""


def dividir(numerador: float, denominador: float, contexto: str) -> float:
    """División protegida: nunca devuelve 0 ni inf para ocultar un denominador nulo."""
    if denominador == 0:
        raise ErrorInterpolacion(f"Denominador igual a cero en {contexto}.")
    return numerador / denominador


class InterpoladorBase(ABC):
    """Interfaz común: resolver(puntos, x_objetivo)."""

    nombre = "Base"
    clave = "base"

    def resolver(self, puntos, x_objetivo) -> dict:
        """Interpola R, G y B en x_objetivo.

        `puntos` es una secuencia de objetos con atributos x, r, g, b
        (por ejemplo PuntoColor). Devuelve un diccionario con los valores
        decimales de cada canal, el procedimiento y el tiempo de cálculo.
        """
        xs, canales, x = self._preparar(puntos, x_objetivo)
        inicio = time.perf_counter()
        valores, procedimiento = self._resolver(xs, canales, x)
        tiempo_ms = (time.perf_counter() - inicio) * 1000.0
        return {
            "metodo": self.nombre,
            "clave": self.clave,
            "x": x,
            "valores": valores,
            "procedimiento": procedimiento,
            "tiempo_ms": tiempo_ms,
        }

    def evaluar(self, puntos, x_objetivo) -> dict:
        """Solo los valores {'r','g','b'} (usado para las muestras del mural)."""
        return self.resolver(puntos, x_objetivo)["valores"]

    @abstractmethod
    def _resolver(self, xs: list[float], canales: dict[str, list[float]], x: float):
        """Devuelve (valores_por_canal, procedimiento)."""

    @staticmethod
    def _preparar(puntos, x_objetivo):
        puntos = list(puntos)
        if len(puntos) < 2:
            raise ErrorInterpolacion("Se necesitan al menos dos puntos para interpolar.")
        try:
            xs = [float(p.x) for p in puntos]
            x = float(x_objetivo)
        except (TypeError, ValueError) as exc:
            raise ErrorInterpolacion("Las posiciones deben ser numéricas.") from exc
        if not all(math.isfinite(v) for v in xs) or not math.isfinite(x):
            raise ErrorInterpolacion("Las posiciones deben ser números finitos.")
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                if xs[i] == xs[j]:
                    raise ErrorInterpolacion(
                        f"Las posiciones x{i} y x{j} se repiten ({xs[i]:g} m): "
                        "el denominador x_i - x_j sería cero."
                    )
        canales = {c: [float(getattr(p, c)) for p in puntos] for c in CANALES}
        return xs, canales, x
