"""Dopasowywanie linii z PO do wierszy systemowych i wyliczanie zgodności."""
import re
from typing import List

from .models import PORecord, SystemRow
from .helpers import is_close

FIELDS = [
    'PID', 'NRF Color', 'Color Desc', 'Pack Ratio', 'Entered Qty',
    'Ext Cost $', 'Ext Owned $', 'OWN MU%', 'Price', 'MSRP',
]

HEADERS = (
    [f'{f} (PO)' for f in FIELDS]
    + ['NRF Color (Sys)', 'Color Desc 1st3 (Sys)', 'Pack Ratio (Sys)', 'Entered Qty (Sys)',
       'Ext Cost $ (Sys)', 'Ext Owned $ (Sys)', 'OWN MU% (Sys)', 'Price (Sys)', 'MSRP (Sys)']
    + ['Cancel Date (Sys)', 'Reason (Sys)']
    + [f'{f} Match' for f in FIELDS]
    + ['Notes']
)


def norm_pack(s: str) -> str:
    """Normalizuje pack ratio typu '6-0' -> '6-0', usuwając zera wiodące itp."""
    if not s:
        return ''
    return '-'.join(str(int(p)) for p in s.split('-'))


def match_po(po_data: dict, sys_rows: List[SystemRow], account: str) -> List[dict]:
    """Dla każdej linii z PO znajduje odpowiadające wiersze systemowe i je sumuje.

    Dopasowanie idzie po (styl, kolor NRF, konto). Jeśli dla tej kombinacji
    istnieje w systemie kilka wierszy (np. kilka fal/dat anulowania), wszystkie
    zostają zsumowane - nie ma już filtrowania po konkretnym miesiącu.
    """
    results = []

    for rec in po_data['records']:
        candidates = [
            sr for sr in sys_rows
            if sr.style == rec.pid6 and sr.nrf_color == rec.nrf_color and sr.account == account
        ]
        if not candidates:
            results.append({**rec.as_dict(), 'sys_found': False, 'note': 'No matching system line found'})
            continue

        used = candidates
        notes = []
        if len(used) > 1:
            notes.append(f'{len(used)} system lines aggregated (summed)')

        sys_qty = sum((r.order_qty or 0) for r in used)
        sys_cost = sum((r.amount or 0) for r in used)
        sys_owned = sum((r.msrp or 0) * (r.order_qty or 0) for r in used)
        cancel_dates = sorted(set(u.cancel_date_str for u in used))
        reasons = sorted(set(u.reason for u in used if u.reason))

        results.append({
            **rec.as_dict(),
            'sys_found': True,
            'sys_color_desc3': used[0].color,
            'sys_pack_ratio': norm_pack(used[0].pack_ratio),
            'sys_entered_qty': sys_qty,
            'sys_ext_cost': sys_cost,
            'sys_ext_owned': sys_owned,
            'sys_own_mu': used[0].imu,
            'sys_price': used[0].price,
            'sys_msrp': used[0].msrp,
            'cancel_dates': ', '.join(cancel_dates),
            'sys_reason': ', '.join(reasons),
            'note': '; '.join(notes),
        })

    return results


def compute_checks(rec: dict) -> dict:
    """Zwraca MATCH/MISMATCH dla każdego pola porównywanego z systemem."""
    def flag(ok: bool) -> str:
        return 'MATCH' if ok else 'MISMATCH'

    return {
        'PID': 'MATCH',
        'NRF Color': 'MATCH',
        'Color Desc': flag(rec['color_desc'][:3] == rec.get('sys_color_desc3')),
        'Pack Ratio': flag(rec['pack_ratio'] == rec.get('sys_pack_ratio')),
        'Entered Qty': flag(is_close(rec['entered_qty'], rec.get('sys_entered_qty'))),
        'Ext Cost $': flag(is_close(rec['ext_cost'], rec.get('sys_ext_cost'))),
        'Ext Owned $': flag(is_close(rec['ext_owned'], rec.get('sys_ext_owned'))),
        'OWN MU%': flag(is_close(rec['own_mu'], rec.get('sys_own_mu'))),
        'Price': flag(is_close(rec['price'], rec.get('sys_price'))),
        'MSRP': flag(is_close(rec['msrp'], rec.get('sys_msrp'))),
    }


def decode_reason(reason_str: str, target_month: int) -> str:
    """Rozszyfrowuje kody typu '0615OW' na czytelny opis z flagą LATE/on time."""
    if not reason_str:
        return ''
    parts = [p.strip() for p in reason_str.split(',') if p.strip()]
    out = []
    for p in parts:
        m = re.match(r'^(\d{2})(\d{2})(OW|PO)$', p, re.IGNORECASE)
        if m:
            mm = int(m.group(1))
            dd = m.group(2)
            late = mm > target_month
            out.append(f"{p} (due {m.group(1)}/{dd} - {'LATE' if late else 'on time'})")
        else:
            out.append(p)
    return ', '.join(out)


def po_sys_values(rec: dict) -> dict:
    """Zwraca pary (wartość z PO, wartość z systemu) dla każdego pola - do tabeli."""
    found = rec.get('sys_found')
    return {
        'PID': (rec['pid'], rec['pid6']),
        'NRF Color': (rec['nrf_color'], rec['nrf_color'] if found else ''),
        'Color Desc': (rec['color_desc'], rec.get('sys_color_desc3', '') if found else ''),
        'Pack Ratio': (rec['pack_ratio'], rec.get('sys_pack_ratio', '') if found else ''),
        'Entered Qty': (rec['entered_qty'], rec.get('sys_entered_qty', '') if found else ''),
        'Ext Cost $': (rec['ext_cost'], rec.get('sys_ext_cost', '') if found else ''),
        'Ext Owned $': (rec['ext_owned'], rec.get('sys_ext_owned', '') if found else ''),
        'OWN MU%': (rec['own_mu'], rec.get('sys_own_mu', '') if found else ''),
        'Price': (rec['price'], rec.get('sys_price', '') if found else ''),
        'MSRP': (rec['msrp'], rec.get('sys_msrp', '') if found else ''),
    }
