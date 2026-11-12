"""Resultado completo de una interpolación cromática."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResultadoInterpolacion:
    """Agrupa todo lo que la vista necesita para mostrar un cálculo."""

    metodo: str                      # Nombre legible del método ("Lagrange", ...)
    clave_metodo: str                # Clave interna ("lagrange", ...)
    x_objetivo: float                # Posición calculada (m)
    resultado_decimal: dict          # {"r": float, "g": float, "b": float} sin redondear
    resultado_rgb: dict              # {"r": int, "g": int, "b": int} redondeado y limitado
    hexadecimal: str                 # "#RRGGBB"
    procedimiento: dict              # Términos/tablas del método seleccionado
    mensaje: str                     # Mensaje de validación / interpretación
    correcto: bool = True            # Indicador de cálculo correcto
    animacion: dict = field(default_factory=dict)       # Datos del mural
    tiempo_ms: float = 0.0           # Tiempo de ejecución del servicio
    procedimientos: dict = field(default_factory=dict)  # Procedimiento de los tres métodos
    comparacion: dict = field(default_factory=dict)     # Tabla comparativa
    puntos: list = field(default_factory=list)          # Puntos de control usados
    canales_limitados: list = field(default_factory=list)  # Canales recortados a [0,255]

    def to_dict(self) -> dict:
        return {
            "correcto": self.correcto,
            "metodo": self.metodo,
            "clave_metodo": self.clave_metodo,
            "x_objetivo": self.x_objetivo,
            "resultado_decimal": self.resultado_decimal,
            "resultado_rgb": self.resultado_rgb,
            "hexadecimal": self.hexadecimal,
            "mensaje": self.mensaje,
            "canales_limitados": self.canales_limitados,
            "puntos": self.puntos,
            "procedimiento": self.procedimiento,
            "procedimientos": self.procedimientos,
            "comparacion": self.comparacion,
            "mural": {k: v for k, v in self.animacion.items() if k != "muestras"},
            "muestras_mural": self.animacion.get("muestras", []),
            "tiempo_ms": self.tiempo_ms,
        }
