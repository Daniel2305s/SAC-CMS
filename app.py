import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import json


@st.cache_resource
def load_gsheets():
    creds_dict = json.loads(st.secrets["gcp_service_account"])

    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    return gspread.authorize(creds)


# --- Constantes ---
SHEET_ID = "1LXbDUJBoJWOtKngL7A9RFNBTFnEzRGGZ1GZT7hu0VIw"

ESTADOS = {
    "Pendiente": "🟡 Pendiente",
    "Contactado": "🟢 Contactado",
    "Devuelto": "🤑 Bono OK"
}
ESTADOS_REVERSO = {v: k for k, v in ESTADOS.items()}

# --- Configuración página ---
st.set_page_config(layout="wide", page_title="CRM Reseñas Google")
st.title("⭐ CRM Seguimiento Reseñas Google")

# --- Cargar cliente sheets ---
gc = load_gsheets()
sh = gc.open_by_key(SHEET_ID)
hojas = [ws.title for ws in sh.worksheets()]

# --- Sidebar ---
st.sidebar.title("📦 Canal de Venta")
hoja_seleccionada = st.sidebar.radio("Selecciona canal:", hojas)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filtros")
filtro_estado = st.sidebar.multiselect(
    "Estado:",
    options=list(ESTADOS.values()),
    default=list(ESTADOS.values())
)
filtro_cliente = st.sidebar.text_input("Buscar cliente:")

# --- Cargar datos del canal ---
ws = sh.worksheet(hoja_seleccionada)
data = ws.get_all_values()

if len(data) < 2:
    st.warning(f"La tabla **{hoja_seleccionada}** está vacía.")
    st.stop()

df = pd.DataFrame(data[1:], columns=data[0])
df = df[df["Número de Venta"].str.strip() != ""].reset_index(drop=True)

# Agregar/normalizar columna Estado
if "Estado" not in df.columns:
    df["Estado"] = "Pendiente"
df["Estado"] = df["Estado"].fillna("").apply(
    lambda x: x if x.strip() != "" else "Pendiente"
)

# --- KPIs ---
total = len(df)
pendientes = len(df[df["Estado"] == "Pendiente"])
contactados = len(df[df["Estado"] == "Contactado"])
devueltos = len(df[df["Estado"] == "Devuelto"])

st.header(f"📋 {hoja_seleccionada}")

col1, col2, col3, col4 = st.columns(3)
col1.metric("📦 Total clientes", total)
col2.metric("🟡 Pendientes", pendientes)
col3.metric("🟢 Contactados", contactados)
col4.metric("🤑 Bono OK", devueltos)

st.markdown("---")

# --- Aplicar emojis al DataFrame para mostrar ---
df_visual = df.copy()
df_visual["Estado"] = df_visual["Estado"].map(lambda x: ESTADOS.get(x, x))

# --- Aplicar filtros ---
df_filtrado = df_visual[df_visual["Estado"].isin(filtro_estado)].copy()
if filtro_cliente:
    df_filtrado = df_filtrado[
        df_filtrado["Cliente"].str.contains(filtro_cliente, case=False, na=False)
    ]

st.caption(f"Mostrando {len(df_filtrado)} de {total} registros")

# --- Tabla editable con emojis ---
edited = st.data_editor(
    df_filtrado,
    column_config={
        "Estado": st.column_config.SelectboxColumn(
            "Estado",
            options=list(ESTADOS.values()),
            required=True
        )
    },
    hide_index=True,
    use_container_width=True
)

# --- Botones ---
col_save, col_export = st.columns([1, 4])

if col_save.button("💾 Guardar cambios", type="primary"):
    # Revertir emojis antes de guardar
    edited["Estado"] = edited["Estado"].map(
        lambda x: ESTADOS_REVERSO.get(x, x)
    )
    # Actualizar df original con cambios editados
    for _, row in edited.iterrows():
        mask = df["Número de Venta"] == row["Número de Venta"]
        df.loc[mask, "Estado"] = row["Estado"]

    # Escribir en Google Sheets
    ws.clear()
    ws.update([df.columns.values.tolist()] + df.values.tolist())
    st.success(f"✅ Cambios guardados en **{hoja_seleccionada}**!")
    st.cache_resource.clear()
    st.rerun()

col_export.download_button(
    label="📥 Exportar pendientes CSV",
    data=df[df["Estado"] == "Pendiente"].to_csv(index=False).encode("utf-8"),
    file_name=f"pendientes_{hoja_seleccionada}.csv",
    mime="text/csv"
)