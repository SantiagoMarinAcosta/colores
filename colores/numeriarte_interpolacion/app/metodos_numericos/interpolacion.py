"""Implementación manual de Lagrange, Newton (diferencias divididas) y Neville.

No se usa ninguna biblioteca de interpolación: todas las operaciones están
escritas explícitamente para que el procedimiento pueda revisarse paso a paso.
"""
from __future__ import annotations

from .base import CANALES, ErrorInterpolacion, InterpoladorBase, dividir


class InterpoladorLagrange(InterpoladorBase):
    """P(x) = Σ y_i·L_i(x),  L_i(x) = Π_{j≠i} (x − x_j)/(x_i − x_j)."""

    nombre = "Lagrange"
    clave = "lagrange"

    @staticmethod
    def bases(xs: list[float], x: float) -> list[dict]:
        """Calcula cada polinomio base L_i(x) con sus factores."""
        resultado = []
        for i, xi in enumerate(xs):
            numerador = 1.0
            denominador = 1.0
            factores = []
            for j, xj in enumerate(xs):
                if j == i:
                    continue
                numerador *= (x - xj)
                denominador *= (xi - xj)
                factores.append({"j": j, "xj": xj, "numerador": x - xj, "denominador": xi - xj})
            valor = dividir(numerador, denominador, f"L_{i}(x)")
            resultado.append({
                "i": i, "xi": xi, "factores": factores,
                "numerador": numerador, "denominador": denominador, "valor": valor,
            })
        return resultado

    def _resolver(self, xs, canales, x):
        bases = self.bases(xs, x)
        suma_bases = 0.0
        for base in bases:
            suma_bases += base["valor"]

        valores, por_canal = {}, {}
        for canal in CANALES:
            ys = canales[canal]
            terminos, total = [], 0.0
            for base, y in zip(bases, ys):
                producto = y * base["valor"]
                total += producto
                terminos.append({"i": base["i"], "y": y, "L": base["valor"], "producto": producto})
            valores[canal] = total
            por_canal[canal] = {"valores_y": ys, "terminos": terminos, "resultado": total}

        procedimiento = {
            "tipo": "lagrange", "x": x, "nodos": xs,
            "bases": bases, "suma_bases": suma_bases, "canales": por_canal,
        }
        return valores, procedimiento


class InterpoladorNewton(InterpoladorBase):
    """P(x) = f[x0] + f[x0,x1](x−x0) + f[x0,x1,x2](x−x0)(x−x1) + …"""

    nombre = "Newton"
    clave = "newton"

    @staticmethod
    def tabla_diferencias(xs: list[float], ys: list[float]):
        """Tabla de diferencias divididas. columnas[k][i] = f[x_i, …, x_{i+k}]."""
        n = len(xs)
        columnas = [[float(y) for y in ys]]
        detalles = [[{"i": i, "j": i, "valor": float(y)} for i, y in enumerate(ys)]]
        for orden in range(1, n):
            anterior = columnas[-1]
            columna, detalle = [], []
            for i in range(n - orden):
                numerador = anterior[i + 1] - anterior[i]
                denominador = xs[i + orden] - xs[i]
                valor = dividir(numerador, denominador, f"f[x{i},...,x{i + orden}]")
                columna.append(valor)
                detalle.append({
                    "i": i, "j": i + orden,
                    "superior": anterior[i + 1], "inferior": anterior[i],
                    "x_superior": xs[i + orden], "x_inferior": xs[i],
                    "valor": valor,
                })
            columnas.append(columna)
            detalles.append(detalle)
        coeficientes = [col[0] for col in columnas]
        return columnas, detalles, coeficientes

    @staticmethod
    def evaluar_forma_newton(xs, coeficientes, x):
        """Evalúa Σ a_k Π_{m<k}(x − x_m) guardando cada término."""
        total, producto, terminos = 0.0, 1.0, []
        for k, a in enumerate(coeficientes):
            if k > 0:
                producto *= (x - xs[k - 1])
            termino = a * producto
            total += termino
            terminos.append({"k": k, "coeficiente": a, "producto_nodos": producto, "termino": termino})
        return total, terminos

    def _resolver(self, xs, canales, x):
        valores, por_canal = {}, {}
        for canal in CANALES:
            columnas, detalles, coef = self.tabla_diferencias(xs, canales[canal])
            total, terminos = self.evaluar_forma_newton(xs, coef, x)
            valores[canal] = total
            por_canal[canal] = {
                "valores_y": canales[canal], "columnas": columnas, "detalles": detalles,
                "coeficientes": coef, "terminos": terminos, "resultado": total,
            }
        return valores, {"tipo": "newton", "x": x, "nodos": xs, "canales": por_canal}


class InterpoladorNeville(InterpoladorBase):
    """P_{i,j}(x) = [(x − x_i)P_{i+1,j}(x) − (x − x_j)P_{i,j−1}(x)] / (x_j − x_i)."""

    nombre = "Neville"
    clave = "neville"

    @staticmethod
    def tabla_neville(xs: list[float], ys: list[float], x: float):
        """niveles[k] contiene P_{i,i+k} para i = 0..n−1−k."""
        n = len(xs)
        niveles = [[{"i": i, "j": i, "valor": float(y)} for i, y in enumerate(ys)]]
        for k in range(1, n):
            anterior = niveles[-1]
            nivel = []
            for i in range(n - k):
                j = i + k
                p_sup = anterior[i + 1]["valor"]   # P_{i+1,j}
                p_inf = anterior[i]["valor"]       # P_{i,j-1}
                numerador = (x - xs[i]) * p_sup - (x - xs[j]) * p_inf
                valor = dividir(numerador, xs[j] - xs[i], f"P_{{{i},{j}}}")
                nivel.append({
                    "i": i, "j": j, "xi": xs[i], "xj": xs[j],
                    "p_superior": p_sup, "p_inferior": p_inf,
                    "numerador": numerador, "denominador": xs[j] - xs[i], "valor": valor,
                })
            niveles.append(nivel)
        return niveles

    def _resolver(self, xs, canales, x):
        valores, por_canal = {}, {}
        for canal in CANALES:
            niveles = self.tabla_neville(xs, canales[canal], x)
            resultado = niveles[-1][0]["valor"]
            valores[canal] = resultado
            por_canal[canal] = {"valores_y": canales[canal], "niveles": niveles, "resultado": resultado}
        return valores, {"tipo": "neville", "x": x, "nodos": xs, "canales": por_canal}


METODOS = {
    InterpoladorLagrange.clave: InterpoladorLagrange,
    InterpoladorNewton.clave: InterpoladorNewton,
    InterpoladorNeville.clave: InterpoladorNeville,
}


def obtener_interpolador(clave: str) -> InterpoladorBase:
    """Instancia el interpolador de la clave dada ('lagrange', 'newton', 'neville')."""
    try:
        return METODOS[str(clave).strip().lower()]()
    except KeyError as exc:
        raise ErrorInterpolacion(
            f"Método «{clave}» no reconocido. Use lagrange, newton o neville."
        ) from exc
