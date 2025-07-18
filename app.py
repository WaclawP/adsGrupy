import streamlit as st
import pandas as pd
import numpy as np
import io

def process_allegro_data(df, cts_g1, zwrot_g1, sprzedane_sztuki_g1, ilosc_unikalnych_id_g1,
                         cts_g2, zwrot_g2, sprzedane_sztuki_g2, ilosc_unikalnych_id_g2):
    # Uproszczenie nazw kolumn
    df.rename(columns={
        'Nazwa kampanii': 'kampania',
        'Nazwa grupy reklam': 'grupa',
        'Tytuł klikniętej oferty': 'tytuł',
        'Numer klikniętej oferty': 'id',
        'Wyświetlenia': 'wyswietlenia',
        'Kliknięcia': 'klikniecia',
        'Zainteresowanie': 'z',
        'CPC(PLN)': 'cpc',
        'CTR': 'ctr',
        'Koszt(PLN)': 'koszt',
        'ROAS(PLN)': 'zwrot',
        'Liczba sprzedanych sztuk': 'sztuki',
        'Wartość sprzedaży(PLN)': 'sprzedaz'
    }, inplace=True)

    # Dodanie współczynnika cts
    df['cts'] = df.klikniecia / df.sztuki
    df.replace([np.inf, -np.inf, np.nan], 0, inplace=True)

    # --- Grupa G1 ---
    g1 = df.copy()
    g1 = g1[(g1.cts > 1) & (g1.cts <= cts_g1) & (g1.sztuki <= sprzedane_sztuki_g1) & (g1.zwrot > zwrot_g1)]
    g1.sort_values(by=['zwrot'], ascending=False, inplace=True)
    g1 = g1.drop_duplicates(subset='id')
    g1 = g1.iloc[:ilosc_unikalnych_id_g1]
    g1.reset_index(drop=True, inplace=True)

    # --- Grupa G2 ---
    g2 = df.copy()
    g2 = g2[(g2.cts > cts_g2) & (g2.sztuki <= sprzedane_sztuki_g2) & (g2.zwrot < zwrot_g2)]
    g2.sort_values(by=['zwrot'], ascending=True, inplace=True)
    g2 = g2.drop_duplicates(subset='id')
    g2 = g2.iloc[:ilosc_unikalnych_id_g2]
    g2.reset_index(drop=True, inplace=True)
    g2['link'] = g2.apply(lambda row: f"https://allegro.pl/show_item.php?item={row.id}", axis=1)

    return g1, g2

st.title("Analizator Danych Allegro")

st.write("Wgraj swój plik Excel z danymi Allegro, aby rozpocząć analizę.")

uploaded_file = st.file_uploader("Wybierz plik Excel", type=["xlsx"])

if uploaded_file:
    st.success("Plik został pomyślnie wgrany!")

    # Odczytanie pliku Excel
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0, engine='openpyxl')
        st.write("Podgląd wgranych danych:")
        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Wystąpił błąd podczas wczytywania pliku: {e}")
        st.stop()

    st.sidebar.header("Ustawienia dla Grupy G1")
    cts_g1 = st.sidebar.slider("CTS (mniejszy równy) dla G1:", 1, 100, 20)
    zwrot_g1 = st.sidebar.slider("ZWROT (większy niż) dla G1:", 1, 20, 5)
    sprzedane_sztuki_g1 = st.sidebar.slider("Sprzedane sztuki (mniejszy równy) dla G1:", 1, 50, 10)
    ilosc_unikalnych_id_g1 = st.sidebar.slider("Ilość unikalnych ID dla G1:", 1, 200, 60)

    st.sidebar.header("Ustawienia dla Grupy G2")
    cts_g2 = st.sidebar.slider("CTS (większe) dla G2:", 1, 100, 20)
    zwrot_g2 = st.sidebar.slider("ZWROT (mniejszy niż) dla G2:", 1, 20, 6)
    sprzedane_sztuki_g2 = st.sidebar.slider("Sprzedane sztuki (mniej niż) dla G2:", 1, 50, 10)
    ilosc_unikalnych_id_g2 = st.sidebar.slider("Ilość unikalnych ID dla G2:", 1, 100, 30)

    if st.button("Przeprowadź analizę"):
        st.write("Trwa przetwarzanie danych...")
        g1, g2 = process_allegro_data(df.copy(), cts_g1, zwrot_g1, sprzedane_sztuki_g1, ilosc_unikalnych_id_g1,
                                     cts_g2, zwrot_g2, sprzedane_sztuki_g2, ilosc_unikalnych_id_g2)

        st.subheader("Wyniki Analizy")

        st.write("### Grupa G1 (Promocja)")
        st.write("Oferty z dobrą konwersją, ale małą ilością sprzedaży (duży zwrot i małe wartości CTS).")
        st.dataframe(g1)

        st.write("### Grupa G2 (Oferta)")
        st.write("Oferty, które słabo sobie radzą, a mają w miarę sporo kliknięć (wysokie CTS, niski zwrot).")
        st.dataframe(g2)

        # Przygotowanie pliku do pobrania
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            g1.to_excel(writer, sheet_name='G1 Promocja', index=False)
            g2.to_excel(writer, sheet_name='G2 Oferta', index=False)
        output.seek(0)

        st.download_button(
            label="Pobierz wyniki jako plik Excel (G1_G2.xlsx)",
            data=output,
            file_name="G1_G2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Proszę wgrać plik Excel, aby uruchomić analizę.")
