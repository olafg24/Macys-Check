"""Drobne funkcje pomocnicze.

Kilka z nich (js_number, js_round) świadomie odwzorowuje specyficzne
zachowanie JavaScriptu z oryginalnego narzędzia (np. Number(null) === 0,
Math.round zaokrągla "w górę" przy .5), żeby wyniki liczbowe zgadzały się
z tym, co dawało poprzednie narzędzie przeglądarkowe.
"""
import math
from typing import Optional


def js_number(v) -> float:
    """Odpowiednik JS `Number(v)`: brak/pusty string -> 0, inaczej float lub NaN."""
    if v is None or v == '':
        return 0.0
    try:
        return float(v)
    except (TypeError, ValueError):
        return float('nan')


def is_truthy_number(x: Optional[float]) -> bool:
    """Odpowiednik prawdziwości liczby w JS: 0 i NaN są 'fałszywe'."""
    if x is None:
        return False
    if isinstance(x, float) and math.isnan(x):
        return False
    return x != 0


def js_round(x: float) -> int:
    """Math.round w JS zaokrągla .5 zawsze w górę (nie bankowo jak Python)."""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def round4(x: float) -> float:
    """Zaokrąglenie do 4 miejsc po przecinku, zgodnie z oryginalną logiką."""
    return js_round(x * 10000) / 10000


def num_or_none(v) -> Optional[float]:
    """Konwersja komórki arkusza na float albo None, gdy brak wartości."""
    if v is None or v == '':
        return None
    try:
        f = float(v)
        if math.isnan(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def is_close(a: Optional[float], b: Optional[float], tol: float = 0.01) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tol
