"""Modelo de un punto de control del mural: posición + color."""
from __future__ import annotations

import re
from dataclasses import dataclass

PATRON_HEX = re.compile(r"^#?([0-9A-Fa-f]{6})$")


class ErrorColor(ValueError):
    """Color con formato hexadecimal inválido."""


def normalizar_hex(color) -> str:
    """Devuelve el color en la forma '#RRGGBB' (mayúsculas) o lanza ErrorColor."""
    if color is None or (isinstance(color, str) and not color.strip()):
        raise ErrorColor("El color está vacío.")
    if not isinstance(color, str):
        raise ErrorColor(f"El color {color!r} no es un texto hexadecimal.")
    coincidencia = PATRON_HEX.match(color.strip())
    if not coincidencia:
        raise ErrorColor(
            f"El color «{color}» no tiene formato hexadecimal válido (#RRGGBB)."
        )
    return "#" + coincidencia.group(1).upper()


def hex_a_rgb(color: str) -> tuple[int, int, int]:
    """Convierte '#RRGGBB' en la terna (R, G, B) de enteros 0–255."""
    h = normalizar_hex(color)[1:]
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


@dataclass(frozen=True)
class PuntoColor:
    """Color conocido en una posición x (metros) del mural."""

    x: float
    hexadecimal: str
    r: int
    g: int
    b: int
    nombre: str = ""

    @classmethod
    def desde_hex(cls, x: float, color: str, nombre: str = "") -> "PuntoColor":
        hexadecimal = normalizar_hex(color)
        r, g, b = hex_a_rgb(hexadecimal)
        return cls(float(x), hexadecimal, r, g, b, nombre or hexadecimal)

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self.r, self.g, self.b

    def componente(self, canal: str) -> int:
        """Valor del canal 'r', 'g' o 'b'."""
        return {"r": self.r, "g": self.g, "b": self.b}[canal]

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "color": self.hexadecimal,
            "nombre": self.nombre,
            "rgb": {"r": self.r, "g": self.g, "b": self.b},
        }
