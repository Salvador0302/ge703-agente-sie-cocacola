"""Importes de una línea y de un documento con el redondeo del modelo del EP (Excel: mitad hacia arriba).

`round()` de Python redondea la mitad al par: 14.625 → 14.62, mientras el EP tiene 14.63. Por eso se usa
Decimal con ROUND_HALF_UP, y los importes de los pedidos coinciden centavo a centavo con los del EP.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

IGV = Decimal("0.18")
_CENTIMO = Decimal("0.01")


def a_decimal(valor: float | int | str | Decimal) -> Decimal:
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


def redondear(valor: Decimal) -> Decimal:
    return valor.quantize(_CENTIMO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Importes:
    bruto: Decimal
    descuento: Decimal
    base: Decimal
    igv: Decimal
    total: Decimal

    def __add__(self, otro: Importes) -> Importes:
        return Importes(*(a + b for a, b in zip(self.tupla, otro.tupla)))

    @property
    def tupla(self) -> tuple[Decimal, ...]:
        return (self.bruto, self.descuento, self.base, self.igv, self.total)


CERO = Importes(*(Decimal("0") for _ in range(5)))


def de_linea(cantidad: float | int, precio_unitario: float, descuento_pct: float, tasa_igv: Decimal = IGV) -> Importes:
    bruto = redondear(a_decimal(cantidad) * a_decimal(precio_unitario))
    descuento = redondear(bruto * a_decimal(descuento_pct))
    base = redondear(bruto - descuento)
    igv = redondear(base * a_decimal(tasa_igv))
    return Importes(bruto, descuento, base, igv, redondear(base + igv))


def de_documento(lineas) -> Importes:
    """Suma de las líneas (la cabecera del EP es la suma de su detalle)."""
    total = CERO
    for linea in lineas:
        total = total + de_linea(linea.cantidad, linea.precio_unitario, linea.descuento_pct)
    return total
