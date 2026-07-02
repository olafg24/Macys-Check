"""Struktury danych używane w całej aplikacji.

Trzymanie ich jako dataclass (zamiast luźnych słowników, jak w oryginalnej
wersji JS) daje autouzupełnianie w edytorze i jasno pokazuje, jakie pola
istnieją na każdym etapie przetwarzania.
"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SystemRow:
    """Pojedynczy wiersz z pliku eksportu systemowego (np. OSC)."""
    style: str
    nrf_color: str
    account: str
    color: str
    pack_ratio: str
    order_qty: Optional[float]
    price: Optional[float]
    amount: Optional[float]
    msrp: Optional[float]
    imu: Optional[float]
    reason: str
    cancel_month: Optional[int]
    cancel_date_str: str


@dataclass
class PORecord:
    """Pojedyncza linia towarowa wyczytana z pliku PO."""
    pid: str
    pid6: str
    nrf_color: str
    color_desc: str
    pack_ratio: str
    entered_qty: Optional[float]
    ext_cost: Optional[float]
    ext_owned: Optional[float]
    own_mu: Optional[float]
    price: Optional[float]
    msrp: Optional[float]

    def as_dict(self) -> dict:
        return asdict(self)
