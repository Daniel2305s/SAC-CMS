import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

# Para local y cloud
@st.cache_resource
def load_gsheets():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["GOOGLE_CREDENTIALS"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    gc = gspread.authorize(creds)
    return gc

gc = load_gsheets()
SHEET_ID = "1LXbDUJBoJWOtKngL7A9RFNBTFnEzRGGZ1GZT7hu0VIw"

st.title("CRM Reseñas ML")

hoja = st.sidebar.selectbox("Tabla", [ws.title for ws in gc.open_by_key(SHEET_ID).worksheets()])

ws = gc.open_by_key(SHEET_ID).worksheet(hoja)
df = pd.DataFrame(ws.get_all_values()[1:], columns=ws.get_all_values()[0])

if "Estado" not in df.columns:
    df["Estado"] = "Pendiente"

edited = st.data_editor(df, column_config={"Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Contactado"])})

if st.button("Guardar"):
    ws.clear()
    ws.update([edited.columns.tolist()] + edited.values.tolist())
    st.success("✅ Guardado")
