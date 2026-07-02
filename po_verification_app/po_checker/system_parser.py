"""Wczytywanie pliku eksportu systemowego (np. OSC export).

W odróżnieniu od pliku PO, ten plik ma prostą, jednowierszową strukturę
nagłówka, więc do parsowania używamy pandas zamiast ręcznego przechodzenia
po komórkach.
"""
from datetime import datetime
from typing import List, Optional

import pandas as pd

from .models import SystemRow
from .helpers import num_or_none


def _parse_cancel_month(value) -> Optional[int]:
    """Wyciąga numer miesiąca z 'Cancel Date' (obsługuje datetime i tekst M/D/RRRR)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.month
    parts = str(value).split('/')
    if len(parts) != 3:
        return None
    try:
        return int(parts[0])
    except ValueError:
        return None


def _format_cancel_date(value) -> str:
    """Formatuje 'Cancel Date' do jednolitego stringa M/D/RRRR (do wyświetlenia)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ''
    if isinstance(value, (datetime, pd.Timestamp)):
        return f'{value.month}/{value.day}/{value.year}'
    return str(value)


def load_system_rows(file_bytes: bytes) -> List[SystemRow]:
    """Wczytuje wiersze systemowe z surowych bajtów pliku .xlsx.

    Odpowiednik `loadSystemRows` z oryginalnego JS: pierwszy wiersz arkusza
    jest pomijany (tytuł), drugi traktowany jako nagłówek kolumn. Jeśli
    istnieje kolumna 'Division', zostają tylko wiersze z wartością 'F'.
    """
    df = pd.read_excel(pd.io.common.BytesIO(file_bytes), header=1, dtype=object)

    if 'Division' in df.columns:
        df = df[df['Division'] == 'F']

    rows: List[SystemRow] = []
    for _, r in df.iterrows():
        cancel_raw = r.get('Cancel Date')
        rows.append(SystemRow(
            style=str(r['Style']) if pd.notna(r.get('Style')) else '',
            nrf_color=str(r['NRF Color']) if pd.notna(r.get('NRF Color')) else '',
            account=str(r['Account']) if pd.notna(r.get('Account')) else '',
            color=str(r['Color']) if pd.notna(r.get('Color')) else '',
            pack_ratio=str(r['Pack Ratio']) if pd.notna(r.get('Pack Ratio')) else '',
            order_qty=num_or_none(r.get('Order Quantity')),
            price=num_or_none(r.get('Price')),
            amount=num_or_none(r.get('Amount')),
            msrp=num_or_none(r.get('MSRP')),
            imu=num_or_none(r.get('IMU%')),
            reason=str(r['Reason']) if pd.notna(r.get('Reason')) else '',
            cancel_month=_parse_cancel_month(cancel_raw),
            cancel_date_str=_format_cancel_date(cancel_raw),
        ))
    return rows
