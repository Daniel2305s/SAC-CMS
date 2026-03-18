import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

@st.cache_resource
def load_gsheets():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["connections.gsheets"]["GOOGLE_CREDENTIALS"]
    )
    gc = gspread.authorize(creds)
    return gc

gc = load_gsheets()
SHEET_ID = "1LXbDUJBoJWOtKngL7A9RFNBTFnEzRGGZ1GZT7hu0VIw"

st.title("CRM Reseñas Mercado Libre")

sh = gc.open_by_key(SHEET_ID)
hoja = st.sidebar.selectbox("Tabla", [ws.title for ws in sh.worksheets()])

ws = sh.worksheet(hoja)
data = ws.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

if "Estado" not in df.columns:
    df["Estado"] = "Pendiente"

edited = st.data_editor(df, column_config={
    "Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Contactado"])
})

if st.button("💾 Guardar cambios"):
    ws.clear()
    ws.update([edited.columns.values.tolist()] + edited.values.tolist())
    st.success("Guardado en Google Sheets!")
