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

**Numer PO** jest czytany automatycznie z treści pliku (linijka w stylu
`PO #: 7588488   Dept: 451   Vendor: 491...`, generowana przez system
źródłowy FedBuy) — nazwa pliku nie ma znaczenia.

**Konto (Store / .com)** nie jest zapisane nigdzie w pliku PO, więc
użytkownik wybiera je ręcznie w aplikacji (rozwijana lista) dla każdego
wgranego pliku PO.

**Dopasowanie do systemu** odbywa się po (styl, kolor NRF, konto). Jeśli dla
tej kombinacji istnieje w systemie kilka wierszy (np. kilka fal/dat
anulowania), wszystkie zostają zsumowane — nie ma filtrowania po konkretnym
miesiącu.

Jeśli Twoje pliki mają inny układ kolumn niż opisany wyżej, zmiany
wystarczy wprowadzić w `po_checker/po_parser.py`.

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
