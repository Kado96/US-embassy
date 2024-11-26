import streamlit as st
import pandas as pd
import requests
import io
from datetime import timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration de la page Streamlit
st.set_page_config(page_title="US", page_icon="🌍", layout="wide")
st.header(":bar_chart: US Dashboard")
st.markdown('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

# URL de l'API et clé d'authentification
api_url = "https://kf.kobotoolbox.org/api/v2/assets/a5L2YdhgWi4PMxDNYNPzPD/data/?format=json"
headers = {
    "Authorization": "Token c700251b23afcdc188fcd30c68274996797149fd"
}

# Fonction pour télécharger les données depuis KoboCollect
@st.cache_data
def download_kobo_data(api_url, headers):
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))
        response = session.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return pd.json_normalize(data.get("results", []))
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

# Télécharger les données
st.info("Chargement des données...")
df_kobo = download_kobo_data(api_url, headers)

if not df_kobo.empty:
    st.success("Données KoboCollect récupérées avec succès!")

    # Conversion de la colonne _submission_time en datetime
    if "_submission_time" in df_kobo.columns:
        df_kobo["_submission_time"] = pd.to_datetime(df_kobo["_submission_time"], errors="coerce")

    # Sidebar pour filtrer par date
    st.sidebar.header("Filtrage par date")
    date1 = st.sidebar.date_input("Date de début", value=pd.to_datetime("2024-01-01"))
    date2 = st.sidebar.date_input("Date de fin", value=pd.to_datetime("2024-12-31"))

    date1 = pd.to_datetime(date1)
    date2 = pd.to_datetime(date2) + timedelta(days=1) - timedelta(seconds=1)

    # Filtrage par plage de dates
    df_filtered = df_kobo[(df_kobo["_submission_time"] >= date1) & (df_kobo["_submission_time"] <= date2)]

    # Colonnes disponibles dans les données
    available_columns = df_filtered.columns.tolist()

    # Uniformiser les types de données pour les colonnes filtrables
    st.sidebar.header("Filtres supplémentaires :")
    filter_columns = {
        "Identification/Province": "Province",
        "Identification/Commune": "Commune",
        "Identification/Adresse_PDV": "Adresse PDV",
        "Nom": "Agent",
        "commandes_credits": "Commandes Credits"
    }

    for col, label in filter_columns.items():
        if col in available_columns:
            df_filtered[col] = df_filtered[col].fillna("").astype(str)
            selected = st.sidebar.multiselect(label, sorted(df_filtered[col].unique()))
            if selected:
                df_filtered = df_filtered[df_filtered[col].isin(selected)]

    # Affichage des données filtrées
    st.write("### Données filtrées :", len(df_filtered))
    st.dataframe(df_filtered)

    # Exporter les données filtrées au format Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_filtered.to_excel(writer, index=False, sheet_name="Données filtrées")

    processed_data = output.getvalue()

    st.download_button(
        label="📥 Télécharger les données filtrées en format Excel",
        data=processed_data,
        file_name="données_filtrées.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
else:
    st.warning("Aucune donnée n'a été récupérée. Veuillez vérifier votre URL ou votre clé API.")
