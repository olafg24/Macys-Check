# PO vs System Verification

Aplikacja Streamlit do porównywania linii z plików PO (zamówienia) z eksportem
z systemu (np. OSC). Wgrywasz raz plik systemowy, potem dowolną liczbę plików
PO — aplikacja dopasowuje pozycje po stylu/kolorze/koncie, pokazuje MATCH/
MISMATCH dla każdego pola i pozwala pobrać kolorowany raport Excel.

To jest przepisana na Python + pandas/openpyxl wersja wcześniejszego narzędzia
działającego w 100% w przeglądarce (HTML/JS). Logika dopasowania i wszystkie
reguły biznesowe zostały zachowane 1:1.

## Uruchomienie lokalnie

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Struktura projektu

```
app.py                     # UI Streamlit
po_checker/
  models.py                # struktury danych (SystemRow, PORecord)
  helpers.py                # pomocnicze funkcje numeryczne
  system_parser.py          # wczytywanie pliku eksportu systemowego (pandas)
  po_parser.py               # wczytywanie pliku PO (openpyxl, struktura wielowierszowa)
  matcher.py                 # dopasowanie PO <-> system, obliczanie MATCH/MISMATCH
  export.py                  # generowanie kolorowanego raportu .xlsx
requirements.txt
```

## Założenia dot. formatu plików

**Plik systemowy** — pierwszy wiersz jest pomijany (tytuł), drugi to nagłówek
kolumn. Wymagane kolumny: `Style`, `NRF Color`, `Account`, `Color`,
`Pack Ratio`, `Order Quantity`, `Price`, `Amount`, `MSRP`, `IMU%`, `Reason`,
`Cancel Date`. Jeśli istnieje kolumna `Division`, zostają tylko wiersze `F`.

**Plik PO** — nagłówek rozciągnięty na dwa wiersze, kolumna A zawiera PID
(styl produktu), a każda pozycja towarowa zajmuje dwa kolejne wiersze: dane
(kolor, ilość, koszt...) i rozbicie kartonu (pack ratio) w wierszu poniżej.

**Nazwa pliku PO** musi pasować do wzorca `..._Miesiac_COM/HAF/STORE.xlsx`,
np. `PO_12345_July_COM.xlsx`. Z nazwy wyciągany jest numer PO, konto
(`M075M` dla STORE/ST, `M094M` dla pozostałych) oraz docelowy miesiąc
(miesiąc z nazwy minus 1).

Jeśli Twoje pliki mają inny format nazw lub inny układ kolumn, zmiany
wystarczy wprowadzić w `po_checker/po_parser.py` (funkcja
`parse_filename_meta` i `parse_po_workbook`).

## Deploy na Streamlit Community Cloud

1. Wrzuć repo na GitHub.
2. Wejdź na [share.streamlit.io](https://share.streamlit.io), wskaż repo i
   plik `app.py`.
3. Gotowe — Streamlit sam zainstaluje zależności z `requirements.txt`.

## Testy

W repo nie ma jeszcze zautomatyzowanych testów jednostkowych. Logika była
ręcznie zweryfikowana na syntetycznych plikach xlsx odwzorowujących format
opisany wyżej. Warto dodać `pytest` + kilka przykładowych plików w
`sample_data/`, zanim narzędzie trafi do szerszego użytku.
