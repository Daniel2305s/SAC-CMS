import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import json

import json

@st.cache_resource
def load_gsheets():
    creds_dict = json.loads(st.secrets["gcp_service_account"])

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    return gspread.authorize(creds)


gc = load_gsheets()
SHEET_ID = "1LXbDUJBoJWOtKngL7A9RFNBTFnEzRGGZ1GZT7hu0VIw"

st.set_page_config(layout="wide", page_title="CRM Reseñas Google")
st.title("⭐ CRM Seguimiento Reseñas Google")

sh = gc.open_by_key(SHEET_ID)
hojas = [ws.title for ws in sh.worksheets()]

# Sidebar con selección de canal
st.sidebar.title("📦 Canal de Venta")
hoja_seleccionada = st.sidebar.radio("Selecciona canal:", hojas)

# Cargar datos del canal seleccionado
ws = sh.worksheet(hoja_seleccionada)
data = ws.get_all_values()

if len(data) < 2:
    st.warning(f"La tabla **{hoja_seleccionada}** está vacía.")
    st.stop()

df = pd.DataFrame(data[1:], columns=data[0])
df = df[df["Número de Venta"].str.strip() != ""].reset_index(drop=True)

if "Estado" not in df.columns:
    df["Estado"] = ""

df["Estado"] = df["Estado"].fillna("").replace("", "Pendiente")

# --- KPIs del canal ---
total = len(df)
pendientes = len(df[df["Estado"] == "Pendiente"])
contactados = len(df[df["Estado"] == "Contactado"])

st.header(f"📋 {hoja_seleccionada}")

col1, col2, col3 = st.columns(3)
col1.metric("Total clientes", total)
col2.metric("⏳ Pendientes", pendientes)
col3.metric("✅ Contactados", contactados)

# --- Filtros ---
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")
filtro_estado = st.sidebar.multiselect(
    "Estado:", ["Pendiente", "Contactado"], default=["Pendiente", "Contactado"]
)
filtro_cliente = st.sidebar.text_input("Buscar cliente:")

df_filtrado = df[df["Estado"].isin(filtro_estado)]
if filtro_cliente:
    df_filtrado = df_filtrado[
        df_filtrado["Cliente"].str.contains(filtro_cliente, case=False, na=False)
    ]

st.caption(f"Mostrando {len(df_filtrado)} de {total} registros")

# --- Tabla editable ---
edited = st.data_editor(
    df_filtrado,
    column_config={
        "Estado": st.column_config.SelectboxColumn(
            "Estado",
            options=["Pendiente", "Contactado"],
            required=True
        )
    },
    hide_index=True,
    use_container_width=True
)

# --- Guardar ---
col_save, col_export = st.columns([1, 4])

if col_save.button("💾 Guardar cambios", type="primary"):
    # Actualizar solo filas editadas en el df original
    for idx, row in edited.iterrows():
        df.loc[df["Número de Venta"] == row["Número de Venta"], "Estado"] = row["Estado"]
    
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    st.success(f"✅ Cambios guardados en **{hoja_seleccionada}**!")
    st.cache_resource.clear()
    st.rerun()

# --- Exportar pendientes ---
if col_export.download_button(
    "📥 Exportar pendientes CSV",
    data=df[df["Estado"] == "Pendiente"].to_csv(index=False).encode("utf-8"),
    file_name=f"pendientes_{hoja_seleccionada}.csv",
    mime="text/csv"
):
    pass