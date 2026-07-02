"""Budowanie pobieralnego raportu .xlsx z podświetlonymi rozbieżnościami."""
from io import BytesIO
from typing import List

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from .matcher import FIELDS, HEADERS, compute_checks, decode_reason, po_sys_values

GREEN = 'FFC6EFCE'
RED = 'FFFFC7CE'
YELLOW = 'FFFFEB9C'
NAVY = 'FF1F4E78'

FIELD_WIDTHS = [12, 10, 8, 10, 10, 8, 13, 13, 8, 13, 13, 8,
                12, 12, 8, 12, 12, 8, 13, 13, 8, 9, 9, 8, 9, 9, 8, 9, 9, 8]
TAIL_WIDTHS = [13, 20, 32, 40]


def _fmt(v):
    return '' if v is None or v == '' else v


def build_excel_report(po_data: dict, results: List[dict]) -> BytesIO:
    """Zwraca bufor BytesIO gotowy do pobrania przez st.download_button."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'PO vs System Verification'

    ws.append(HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFFFF', name='Arial')
        cell.fill = PatternFill('solid', fgColor=NAVY)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    n_field_cols = len(FIELDS) * 3

    for rec in results:
        vals = po_sys_values(rec)
        row_data = []
        for f in FIELDS:
            po_v, sys_v = vals[f]
            row_data.append(_fmt(po_v))
            row_data.append(_fmt(sys_v) if rec['sys_found'] else '')
            row_data.append('')

        reason_interp = decode_reason(rec.get('sys_reason', ''), po_data['target_month']) if rec['sys_found'] else ''
        row_data.append(rec.get('cancel_dates', '') if rec['sys_found'] else '')
        row_data.append(rec.get('sys_reason', '') if rec['sys_found'] else '')
        row_data.append(reason_interp)
        row_data.append(rec.get('note') or ('' if rec['sys_found'] else 'No matching system line found'))

        ws.append(row_data)
        row = ws[ws.max_row]

        if not rec['sys_found']:
            for cell in row:
                cell.fill = PatternFill('solid', fgColor=RED)
            continue

        checks = compute_checks(rec)
        for idx, f in enumerate(FIELDS):
            match_col = idx * 3 + 3  # 1-indexed
            cell = row[match_col - 1]
            cell.value = checks[f]
            cell.fill = PatternFill('solid', fgColor=GREEN if checks[f] == 'MATCH' else RED)
            cell.alignment = Alignment(horizontal='center')

        if 'LATE' in reason_interp:
            row[n_field_cols + 2].fill = PatternFill('solid', fgColor=YELLOW)
        if rec.get('note'):
            row[n_field_cols + 3].fill = PatternFill('solid', fgColor=YELLOW)

    widths = FIELD_WIDTHS + TAIL_WIDTHS
    for i, col_cells in enumerate(ws.columns):
        letter = col_cells[0].column_letter
        ws.column_dimensions[letter].width = widths[i] if i < len(widths) else 12

    ws.freeze_panes = 'A2'

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
