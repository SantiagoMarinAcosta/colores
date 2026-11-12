"""Controlador del glosario: entrega los términos a la vista."""
from flask import Blueprint, render_template

bp = Blueprint("glosario", __name__)

CATEGORIAS = {
    "interpolacion": "Interpolación",
    "metodos": "Métodos",
    "color": "Color",
    "numerico": "Cálculo numérico",
    "arte": "Arte digital",
}

TERMINOS = [
    ("Interpolación", "interpolacion",
     "Estimación de valores desconocidos situados entre puntos conocidos, mediante una función que pasa exactamente por esos puntos."),
    ("Punto conocido", "interpolacion",
     "Par (x, y) cuyo valor se conoce de antemano. En el mural: una posición en metros y el color elegido por el artista."),
    ("Posición objetivo", "interpolacion",
     "Valor de x donde se desea estimar el color. Debe estar entre el menor y el mayor nodo para que sea interpolación y no extrapolación."),
    ("Polinomio interpolador", "interpolacion",
     "Polinomio de grado ≤ n que pasa por los n + 1 puntos conocidos. Es único: Lagrange, Newton y Neville lo construyen o evalúan de formas distintas."),
    ("Nodo", "interpolacion",
     "Cada abscisa xᵢ de un punto conocido. En el ejemplo los nodos son 0, 3 y 6 metros."),
    ("Lagrange", "metodos",
     "Método que escribe el polinomio como P(x) = Σ yᵢ·Lᵢ(x), donde cada base Lᵢ vale 1 en su nodo y 0 en los demás."),
    ("Diferencias divididas", "metodos",
     "Cocientes recursivos f[xᵢ,…,xⱼ] = (f[xᵢ₊₁,…,xⱼ] − f[xᵢ,…,xⱼ₋₁]) / (xⱼ − xᵢ) que forman los coeficientes del polinomio de Newton."),
    ("Newton", "metodos",
     "Forma del polinomio interpolador P(x) = f[x₀] + f[x₀,x₁](x−x₀) + … construida con diferencias divididas. Permite agregar puntos sin rehacer todo el cálculo."),
    ("Neville", "metodos",
     "Algoritmo recursivo que combina interpolaciones de menor grado en una tabla triangular para obtener directamente el valor P(x) en un punto."),
    ("RGB", "color",
     "Modelo de color aditivo en el que cada color se describe con tres intensidades: rojo (R), verde (G) y azul (B), normalmente enteros de 0 a 255."),
    ("Canal rojo", "color",
     "Componente R del color. Se interpola como una función independiente R(x)."),
    ("Canal verde", "color",
     "Componente G del color. Se interpola como una función independiente G(x)."),
    ("Canal azul", "color",
     "Componente B del color. Se interpola como una función independiente B(x)."),
    ("Color hexadecimal", "color",
     "Notación #RRGGBB que escribe cada canal en base 16 con dos dígitos. Ejemplo: (80, 52, 184) = #5034B8."),
    ("Degradado", "arte",
     "Transición gradual entre dos o más colores a lo largo de una superficie."),
    ("Distribución cromática", "arte",
     "Asignación de un color a cada posición del mural; aquí se obtiene evaluando R(x), G(x) y B(x) en muchas posiciones."),
    ("Arte digital", "arte",
     "Producción artística que usa la computadora como herramienta, donde los colores y formas se representan como datos numéricos."),
    ("Precisión", "numerico",
     "Cantidad de cifras significativas con que se representa un número. Los cálculos internos usan doble precisión y se muestran con cinco decimales."),
    ("Redondeo", "numerico",
     "Aproximar un número a una cantidad fija de cifras. Los canales se redondean al entero más cercano solo al final, nunca durante el procedimiento."),
    ("Clamp o limitación", "numerico",
     "Operación que recorta un valor al intervalo permitido: clamp(v) = mín(255, máx(0, v)). Evita colores inválidos cuando el polinomio sale de [0, 255]."),
    ("Extrapolación", "interpolacion",
     "Estimar valores fuera del intervalo de los nodos. Es menos confiable que la interpolación, por eso la aplicación la rechaza."),
    ("Fenómeno de Runge", "numerico",
     "Oscilación de polinomios de grado alto entre nodos equiespaciados. Es una razón para usar pocos puntos o interpolación por tramos."),
]


@bp.get("/glosario")
def glosario():
    terminos = sorted(
        ({"termino": t, "categoria": c, "categoria_nombre": CATEGORIAS[c], "definicion": d}
         for t, c, d in TERMINOS),
        key=lambda item: item["termino"].lower(),
    )
    return render_template("glosario.html", terminos=terminos, categorias=CATEGORIAS, pagina="glosario")
