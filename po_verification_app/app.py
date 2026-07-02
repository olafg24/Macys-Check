"""PO vs System Verification - aplikacja Streamlit.

Wczytaj raz plik eksportu systemowego, a następnie sprawdzaj dowolną liczbę
plików PO względem niego. To odpowiednik narzędzia przeglądarkowego (HTML/JS),
przepisany na Python + pandas/openpyxl, żeby dało się go hostować jako
zwykłą aplikację Streamlit.
"""
import pandas as pd
import streamlit as st

from po_checker.system_parser import load_system_rows
from po_checker.po_parser import parse_po_workbook
from po_checker.matcher import match_po, compute_checks, po_sys_values, FIELDS
from po_checker.export import build_excel_report

st.set_page_config(page_title="PO vs System Verification", layout="wide")

MATCH_BG, MATCH_TEXT = "#DCF3E4", "#1E7F4C"
MISMATCH_BG, MISMATCH_TEXT = "#FDEAEA", "#B42318"
NOTE_BG, NOTE_TEXT = "#FFF3D6", "#92620A"


@st.cache_data(show_spinner=False)
def _load_system_rows_cached(file_bytes: bytes):
    return load_system_rows(file_bytes)


@st.cache_data(show_spinner=False)
def _parse_po_cached(file_bytes: bytes, filename: str):
    return parse_po_workbook(file_bytes, filename)


def build_display_dataframe(po_data: dict, results: list) -> pd.DataFrame:
    """Buduje DataFrame w takim samym układzie kolumn jak eksportowany plik Excel."""
    rows = []
    for rec in results:
        vals = po_sys_values(rec)
        checks = compute_checks(rec) if rec['sys_found'] else None
        row = {}
        for f in FIELDS:
            row[f'{f} (PO)'] = vals[f][0]
        for f in FIELDS:
            if f == 'PID':
                continue
            label = 'Color Desc 1st3 (Sys)' if f == 'Color Desc' else f'{f} (Sys)'
            row[label] = vals[f][1] if rec['sys_found'] else ''
        row['Cancel Date (Sys)'] = rec.get('cancel_dates', '') if rec['sys_found'] else ''
        row['Reason (Sys)'] = rec.get('sys_reason', '') if rec['sys_found'] else ''
        for f in FIELDS:
            row[f'{f} Match'] = checks[f] if checks else ''
        row['Notes'] = rec.get('note') or ('' if rec['sys_found'] else 'No matching system line found')
        rows.append(row)
    return pd.DataFrame(rows)


def style_dataframe(df: pd.DataFrame):
    """Koloruje kolumny *Match* oraz komórki z uwagami/spóźnieniami."""
    match_cols = [c for c in df.columns if c.endswith('Match')]

    def color_match(val):
        if val == 'MATCH':
            return f'background-color: {MATCH_BG}; color: {MATCH_TEXT}; font-weight: 600;'
        if val == 'MISMATCH':
            return f'background-color: {MISMATCH_BG}; color: {MISMATCH_TEXT}; font-weight: 600;'
        return ''

    def color_note(val):
        if isinstance(val, str) and val:
            return f'background-color: {NOTE_BG}; color: {NOTE_TEXT};'
        return ''

    styler = df.style
    for col in match_cols:
        styler = styler.map(color_match, subset=[col])
    if 'Notes' in df.columns:
        styler = styler.map(color_note, subset=['Notes'])
    return styler


st.title("PO vs system verification")
st.caption(
    "Wgraj raz plik eksportu systemowego, a następnie sprawdź dowolną liczbę plików PO. "
    "Przetwarzanie odbywa się na serwerze aplikacji Streamlit (nie w przeglądarce, jak w oryginale)."
)

with st.container(border=True):
    st.markdown("**Krok 1 — plik eksportu systemowego**")
    system_file = st.file_uploader("Wgraj plik eksportu OSC (.xlsx)", type=["xlsx"], key="system_file")

    system_rows = None
    if system_file is not None:
        try:
            system_rows = _load_system_rows_cached(system_file.getvalue())
            st.success(f"{len(system_rows):,} wierszy wczytanych".replace(",", " "))
        except Exception as e:
            st.error(f"Błąd wczytywania pliku systemowego: {e}")

ACCOUNT_OPTIONS = {"Store (M075M)": "M075M", ".com (M094M)": "M094M"}

with st.container(border=True):
    st.markdown("**Krok 2 — pliki PO**")
    po_files = st.file_uploader(
        "Wgraj jeden lub więcej plików PO (.xlsx)", type=["xlsx"], accept_multiple_files=True, key="po_files"
    )

    account_choices = {}
    if po_files:
        st.caption("Dla każdego pliku wybierz, na jakie konto został złożony (system tego nie zapisuje w pliku PO):")
        for idx, f in enumerate(po_files):
            account_choices[idx] = st.selectbox(
                f.name, options=list(ACCOUNT_OPTIONS.keys()), key=f"account_{idx}_{f.name}"
            )

    run = st.button("Uruchom weryfikację", disabled=not (system_rows and po_files))

if run and system_rows and po_files:
    for idx, f in enumerate(po_files):
        st.divider()
        try:
            account_code = ACCOUNT_OPTIONS[account_choices[idx]]
            po_data = _parse_po_cached(f.getvalue(), f.name)
            results = match_po(po_data, system_rows, account_code)
            mismatch_count = sum(
                1 for r in results
                if not r['sys_found'] or 'MISMATCH' in compute_checks(r).values()
            )

            badge = f":red[{mismatch_count} linia/linie do sprawdzenia]" if mismatch_count else ":green[Wszystko się zgadza]"
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"PO {po_data['po_number']}")
                st.caption(f"{len(results)} linii · konto {account_choices[idx]} · {badge}")
            with col2:
                report = build_excel_report(po_data, results)
                st.download_button(
                    "Pobierz raport Excel",
                    data=report,
                    file_name=f"PO_{po_data['po_number']}_Verification.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{f.name}",
                )

            df = build_display_dataframe(po_data, results)
            st.dataframe(style_dataframe(df), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"{f.name}: {e}")
elif not system_rows:
    st.info("Zacznij od wgrania pliku eksportu systemowego w kroku 1.")
