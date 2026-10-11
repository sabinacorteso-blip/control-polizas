import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# Configuración de la página con tema visual en Verde Agua
st.set_page_config(page_title="Seguros Casa Pantera - CRM", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #F4FBFB;
    }
    h1, h2, h3 {
        color: #006666;
    }
    .stButton>button {
        background-color: #20B2AA;
        color: white;
        border-radius: 6px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #008080;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def cargar_datos_nube():
    try:
        conn = st.connection("gsheets", type="gsheets")
        df = conn.read(ttl=5)
        if not df.empty:
            return df
    except:
        pass
    
    try:
        return pd.read_csv("cartera_pantera.csv")
    except:
        return pd.DataFrame(columns=[
            "Cliente", "RFC", "Telefono", "Correo", "Nacimiento", "Contrato", 
            "Poliza", "Serie", "Placa", "Aseguradora", "Vendedor", "Ramo", 
            "Uso_Auto", "Prima_Neta", "Forma_Pago", "Vigencia", "Emision", 
            "Vencimiento", "Pago_Limite", "Estatus_Pago", "Estatus_Poliza", "Mes_Venta"
        ])

def guardar_datos_nube(df):
    df.to_csv("cartera_pantera.csv", index=False)
    try:
        conn = st.connection("gsheets", type="gsheets")
        conn.update(data=df)
    except:
        pass
    st.cache_data.clear()

if "clientes" not in st.session_state:
    st.session_state.clientes = cargar_datos_nube()

df = st.session_state.clientes
hoy = datetime.now().date()

df['Vencimiento_dt'] = pd.to_datetime(df.get('Vencimiento'), errors='coerce').dt.date
df['Pago_Limite_dt'] = pd.to_datetime(df.get('Pago_Limite'), errors='coerce').dt.date

# -------------------------------------------------------------
# BARRA LATERAL CON NAVEGACIÓN
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🐆 **CASA PANTERA**")
    st.markdown("---")
    menu = st.selectbox("Menú CRM", [
        "Dashboard del Mes", 
        "Búsqueda de Pólizas", 
        "Registro y Renovación", 
        "Centro de Cobranza & WhatsApp", 
        "Avisos de Cumpleaños", 
        "Reporte Contable (Excel)"
    ])

# -------------------------------------------------------------
# 1. DASHBOARD DEL MES
# -------------------------------------------------------------
if menu == "Dashboard del Mes":
    st.header(f"🌿 Panel de Control - Seguros Casa Pantera ({hoy.strftime('%B %Y')})")
    
    if not df.empty and 'Pago_Limite_dt' in df.columns:
        pend_10d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] >= hoy) & (df['Pago_Limite_dt'] <= hoy + timedelta(days=10))]
        venc_5d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] < hoy) & (df['Pago_Limite_dt'] >= hoy - timedelta(days=5))]
        por_vencer_cov = df[(df['Vencimiento_dt'] >= hoy) & (df['Vencimiento_dt'] <= hoy + timedelta(days=10))]
    else:
        pend_10d = venc_5d = por_vencer_cov = pd.DataFrame()

    col1, col2, col3 = st.columns(3)
    
    vista = "pendientes"
    if col1.button(f"🔔 Pendientes de Pago (10d)\nTotal: {len(pend_10d)}", use_container_width=True):
        vista = "pendientes"
    if col2.button(f"⚠️ Pagos Vencidos\nTotal: {len(venc_5d)}", use_container_width=True):
        vista = "vencidos"
    if col3.button(f"🛡️ Pólizas por Vencer (Cobertura)\nTotal: {len(por_vencer_cov)}", use_container_width=True):
        vista = "vencer"

    st.markdown("---")

    if vista == "pendientes":
        st.subheader("📋 Listado - Pendientes de Pago")
        data_ver = pend_10d
    elif vista == "vencidos":
        st.subheader("📋 Listado - Pagos Vencidos")
        data_ver = venc_5d
    elif vista == "vencer":
        st.subheader("📋 Listado - Pólizas por Vencer y Cobertura")
        data_ver = por_vencer_cov

    if not data_ver.empty:
        t_mostrar = data_ver[['Poliza', 'Cliente', 'Ramo', 'Aseguradora', 'Prima_Neta', 'Pago_Limite', 'Estatus_Poliza']].copy()
        t_mostrar.columns = ['Folio', 'Cliente', 'Cobertura / Ramo', 'Aseguradora', 'Prima Neta', 'Fecha Límite', 'Estatus']
        t_mostrar['Prima Neta'] = t_mostrar['Prima Neta'].apply(lambda x: f"${float(x):,.2f}" if pd.notnull(x) else "$0.00")
        st.dataframe(t_mostrar, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros bajo este criterio en el periodo actual.")

# -------------------------------------------------------------
# 2. BÚSQUEDA DE PÓLIZAS
# -------------------------------------------------------------
elif menu == "Búsqueda de Pólizas":
    st.header("🔍 Búsqueda Inteligente de Pólizas")
    criterio = st.text_input("Buscar por Nombre del Cliente, Serie del Auto o Placa:")
    
    if criterio and not df.empty:
        filtro = df[
            df['Cliente'].str.contains(criterio, case=False, na=False) |
            df['Serie'].str.contains(criterio, case=False, na=False) |
            df['Placa'].str.contains(criterio, case=False, na=False)
        ]
        if not filtro.empty:
            st.success(f"Se encontraron {len(filtro)} coincidencia(s):")
            st.dataframe(filtro[['Poliza', 'Cliente', 'Serie', 'Placa', 'Aseguradora', 'Vencimiento', 'Estatus_Poliza']], use_container_width=True, hide_index=True)
            
            pol_a_borrar = st.selectbox("Seleccione número de póliza a eliminar si es necesario:", filtro['Poliza'].tolist())
            if st.button("🗑️ Eliminar Póliza Seleccionada"):
                df = df[df['Poliza'] != pol_a_borrar].reset_index(drop=True)
                st.session_state.clientes = df
                guardar_datos_nube(df)
                st.success("Póliza eliminada con éxito.")
                st.rerun()
        else:
            st.warning("No se encontraron registros con ese criterio.")

# -------------------------------------------------------------
# 3. REGISTRO Y RENOVACIÓN
# -------------------------------------------------------------
elif menu == "Registro y Renovación":
    st.header("📝 Alta y Renovación de Póliza")
    
    with st.form("form_reg"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo del Cliente").upper()
            rfc = st.text_input("RFC o Texto (Ej. MEMR851015HDF o 720806)").upper()
            
            # --- EXTRACCIÓN INTELIGENTE DE FECHA DE NACIMIENTO ---
            fecha_nac_calc = datetime.today().date()
            limpio = "".join([c for c in rfc if c.isdigit()])
            if len(rfc) >= 10:  # RFC estándar de 13 caracteres (posiciones 4 a 9 son AAMMDD)
                try:
                    a_str, m_str, d_str = rfc[4:6], rfc[6:8], rfc[8:10]
                    siglo = 1900 if int(a_str) > 30 else 2000
                    fecha_nac_calc = datetime(siglo + int(a_str), int(m_str), int(d_str)).date()
                except:
                    pass
            elif len(limpio) >= 6:  # Si ingresa directo 6 dígitos (AAMMDD)
                try:
                    a_str, m_str, d_str = limpio[:2], limpio[2:4], limpio[4:6]
                    siglo = 1900 if int(a_str) > 30 else 2000
                    fecha_nac_calc = datetime(siglo + int(a_str), int(m_str), int(d_str)).date()
                except:
                    pass

            nacimiento = st.date_input("Fecha de Nacimiento (Autocalculada)", value=fecha_nac_calc)
            telefono = st.text_input("Teléfono (10 dígitos)")
            
            st.markdown("**Correo Electrónico**")
            c_user = st.text_input("Escribe el usuario del correo", label_visibility="collapsed", placeholder="usuario")
            c_dom = st.selectbox("Dominio", ["@gmail.com", "@hotmail.com", "@yahoo.com", "Personalizado"])
            correo = c_user if c_dom == "Personalizado" else c_user + c_dom

            contrato = st.text_input("Número de Contrato")
            poliza = st.text_input("Número de Póliza / Folio")
            serie = st.text_input("Número de Serie del Auto")
            placa = st.text_input("Placa del Vehículo")

        with col2:
            aseguradora_op = ["ANA", "AFIRME", "QUÁLITAS", "GENERAL DE SEGUROS", "BANORTE", "GNP", "OTRO"]
            aseg_sel = st.selectbox("Aseguradora", aseguradora_op)
            aseguradora = st.text_input("Especifique Aseguradora") if aseg_sel == "OTRO" else aseg_sel

            vendedor_op = ["ANDRES", "AXEL", "OTRO"]
            vend_sel = st.selectbox("Vendedor / Asesor", vendedor_op)
            vendedor = st.text_input("Especifique Asesor") if vend_sel == "OTRO" else vend_sel

            ramo = st.selectbox("Ramo", ["Auto", "Vida / PPR", "Gastos Médicos Mayores", "Daños"])
            uso_auto = st.selectbox("Uso del Auto", ["Particular", "Taxi", "App", "Colectivo", "Carga"])
            
            prima_neta = st.number_input("Monto Prima Neta ($)", min_value=0.0, format="%.2f")
            
            # --- FORMA DE PAGO ACTUALIZADA ---
            forma_pago = st.selectbox("Forma de Pago", ["Mensual", "Trimestral", "Cuatrimestral", "Semestral", "Anual"])
            
            emision = st.date_input("Fecha de Emisión / Inicio")
            
            # --- VIGENCIAS EXACTAS ---
            vigencia_op = st.selectbox("Vigencia", ["6 meses", "1 año", "2 años"])
            
            if vigencia_op == "6 meses":
                vencimiento_calculado = emision + timedelta(days=180)
            elif vigencia_op == "1 año":
                vencimiento_calculado = emision + timedelta(days=365)
            else:
                vencimiento_calculado = emision + timedelta(days=730)

            vencimiento = st.date_input("Fecha de Vencimiento (Automática)", value=vencimiento_calculado)
            pago_limite = st.date_input("Fecha Límite de Pago")
            
            estatus_pago = st.selectbox("Estatus de Pago", ["Pendiente", "Pagada"])
            estatus_poliza = st.selectbox("Estatus de Póliza", ["Activa", "Cancelada"])
            mes_venta = st.selectbox("Mes de Contabilidad", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])

        submitted = st.form_submit_button("Guardar Registro Compartido")

        if submitted and nombre:
            if not df.empty and 'Poliza' in df.columns:
                df = df[df['Poliza'] != poliza].reset_index(drop=True)

            nuevo = {
                "Cliente": nombre, "RFC": rfc, "Telefono": telefono, "Correo": correo,
                "Nacimiento": str(nacimiento), "Contrato": contrato, "Poliza": poliza,
                "Serie": serie, "Placa": placa, "Aseguradora": aseguradora, "Vendedor": vendedor,
                "Ramo": ramo, "Uso_Auto": uso_auto, "Prima_Neta": prima_neta, "Forma_Pago": forma_pago,
                "Vigencia": vigencia_op, "Emision": str(emision), "Vencimiento": str(vencimiento), 
                "Pago_Limite": str(pago_limite), "Estatus_Pago": estatus_pago, "Estatus_Poliza": estatus_poliza, 
                "Mes_Venta": mes_venta
            }
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            st.session_state.clientes = df
            guardar_datos_nube(df)
            st.success("¡Registro guardado y sincronizado con éxito para todo tu equipo!")

# -------------------------------------------------------------
# 4. CENTRO DE COBRANZA & WHATSAPP
# -------------------------------------------------------------
elif menu == "Centro de Cobranza & WhatsApp":
    st.header("💬 Envío de Mensajes por WhatsApp")
    if not df.empty and 'Estatus_Pago' in df.columns:
        pendientes = df[df['Estatus_Pago'] == 'Pendiente']
        if not pendientes.empty:
            for idx, row in pendientes.iterrows():
                with st.expander(f"📌 {row['Cliente']} | Póliza: {row['Poliza']} ({row['Aseguradora']})"):
                    st.write(f"**Forma de Pago:** {row['Forma_Pago']} | **Límite:** {row['Pago_Limite']} | **Prima Neta:** ${float(row['Prima_Neta']):,.2f}")
                    msg = f"Hola {row['Cliente']}, le saludamos de Seguros Casa Pantera. Le recordamos que su pago ({row['Forma_Pago']}) de la póliza {row['Poliza']} vence el {row['Pago_Limite']}. Quedamos a sus órdenes."
                    link = f"https://wa.me/52{row['Telefono']}?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#20B2AA; color:white; padding:8px 16px; border-radius:4px;">💬 Enviar WhatsApp de Cobranza</button></a>', unsafe_allow_html=True)
        else:
            st.success("No hay cobros pendientes.")
    else:
        st.info("No hay registros cargados aún.")

# -------------------------------------------------------------
# 5. AVISOS DE CUMPLEAÑOS
# -------------------------------------------------------------
elif menu == "Avisos de Cumpleaños":
    st.header("🎂 Avisos de Cumpleaños Automatizados")
    if not df.empty and 'Nacimiento' in df.columns:
        mes_actual = hoy.month
        df['Mes_C'] = pd.to_datetime(df['Nacimiento'], errors='coerce').dt.month
        cumples = df[df['Mes_C'] == mes_actual]

        if not cumples.empty:
            for idx, row in cumples.iterrows():
                st.write(f"🎈 **{row['Cliente']}** — Nacimiento: {row['Nacimiento']} — Tel: {row['Telefono']}")
                msg_c = f"¡Muchas felicidades en tu cumpleaños de parte de Seguros Casa Pantera! 🥳 Te deseamos el mayor de los éxitos."
                link_c = f"https://wa.me/52{row['Telefono']}?text={urllib.parse.quote(msg_c)}"
                st.markdown(f'<a href="{link_c}" target="_blank"><button style="background-color:#20B2AA; color:white; padding:6px 12px; border-radius:4px;">🎁 Enviar Felicitación</button></a>', unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No hay cumpleaños registrados este mes.")

# -------------------------------------------------------------
# 6. REPORTE CONTABLE EN EXCEL
# -------------------------------------------------------------
elif menu == "Reporte Contable (Excel)":
    st.header("📈 Generación de Excel de Contabilidad Mensual")
    mes_rep = st.selectbox("Selecciona Mes Contable", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=9)
    
    if not df.empty and 'Mes_Venta' in df.columns:
        df_rep = df[df['Mes_Venta'] == mes_rep]
        st.dataframe(df_rep[['Poliza', 'Cliente', 'Contrato', 'Aseguradora', 'Vendedor', 'Prima_Neta', 'Forma_Pago', 'Estatus_Pago']], use_container_width=True)
        
        if not df_rep.empty:
            total_m = df_rep['Prima_Neta'].astype(float).sum()
            st.metric("Prima Neta Total del Mes", f"${total_m:,.2f}")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_rep.to_excel(writer, index=False, sheet_name='Contabilidad_Mensual')
            
            st.download_button(
                label=f"📥 Descargar Reporte Contable - {mes_rep}",
                data=output.getvalue(),
                file_name=f"Contabilidad_Casa_Pantera_{mes_rep}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No hay registros contables para este mes.")
