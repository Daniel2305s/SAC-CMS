import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

@st.cache_resource
def load_gsheets():
    creds_dict = dict(st.secrets)
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    creds = service_account.Credentials.from_service_account_info(creds_dict)
    
    return gspread.authorize(creds)

    creds = service_account.Credentials.from_service_account_info(creds_dict)
    return gspread.authorize(creds)

gc = load_gsheets()
SHEET_ID = "1LXbDUJBoJWOtKngL7A9RFNBTFnEzRGGZ1GZT7hu0VIw"

st.title("CRM Reseñas Mercado Libre")

try:
    sh = gc.open_by_key(SHEET_ID)
    hojas = [ws.title for ws in sh.worksheets()]
    hoja = st.sidebar.selectbox("Selecciona tabla:", hojas)
    
    ws = sh.worksheet(hoja)
    data = ws.get_all_values()
    if len(data) > 1:
        df = pd.DataFrame(data[1:], columns=data[0])
        if "Estado" not in df.columns:
            df["Estado"] = "Pendiente"
        
        edited = st.data_editor(df, column_config={
            "Estado": st.column_config.SelectboxColumn(options=["Pendiente", "Contactado"])
        })
        
        if st.button("💾 Guardar"):
            ws.clear()
            ws.update([edited.columns.values.tolist()] + edited.values.tolist())
            st.success("✅ Cambios guardados!")
    else:
        st.warning("La hoja está vacía.")
except Exception as e:
    st.error(f"Error conectando: {e}")
