import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import urllib.parse

# Configuración de la página con tema visual en Verde Agua
st.set_page_config(page_title="Seguros Casa Pantera - CRM", layout="wide")

# Estilos CSS personalizados para aplicar tonos Verde Agua (#008080, #20B2AA, #E0F2F1)
st.markdown("""
    <style>
    .stApp {
        background-color: #F4FBFB;
    }
    .css-18e3th9 {
        background-color: #E0F2F1;
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

# Simulación de base de datos inicial
hoy = datetime.now().date()

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame([
        {
            "Cliente": "RAFAEL MENDOZA MEDINA",
            "RFC": "MEMR851015HDF",
            "Telefono": "5512345678",
            "Correo": "rafael@gmail.com",
            "Nacimiento": "1985-10-15",
            "Contrato": "CTR-9821",
            "Poliza": "20275830",
            "Serie": "3VW123456789",
            "Placa": "ABC-123-A",
            "Aseguradora": "QUÁLITAS",
            "Vendedor": "ANDRES",
            "Ramo": "Auto",
            "Uso_Auto": "Particular",
            "Prima_Neta": 4500.0,
            "Forma_Pago": "Contado",
            "Emision": str(hoy - timedelta(days=60)),
            "Vencimiento": str(hoy + timedelta(days=5)),
            "Pago_Limite": str(hoy + timedelta(days=5)),
            "Estatus_Pago": "Pendiente",
            "Estatus_Poliza": "Activa",
            "Mes_Venta": "Octubre"
        }
    ])

if "historico" not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=st.session_state.clientes.columns)

# -------------------------------------------------------------
# BARRA LATERAL CON LOGO Y NAVEGACIÓN
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

df = st.session_state.clientes
df['Vencimiento_dt'] = pd.to_datetime(df['Vencimiento']).dt.date
df['Pago_Limite_dt'] = pd.to_datetime(df['Pago_Limite']).dt.date

# -------------------------------------------------------------
# 1. DASHBOARD DEL MES (VENTANAS EMERGENTES / ACCESO A INFORMACIÓN)
# -------------------------------------------------------------
if menu == "Dashboard del Mes":
    st.header(f"🌿 Panel de Control - Seguros Casa Pantera ({hoy.strftime('%B %Y')})")
    
    pend_10d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] >= hoy) & (df['Pago_Limite_dt'] <= hoy + timedelta(days=10))]
    venc_5d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] < hoy) & (df['Pago_Limite_dt'] >= hoy - timedelta(days=5))]
    por_vencer_cov = df[(df['Vencimiento_dt'] >= hoy) & (df['Vencimiento_dt'] <= hoy + timedelta(days=10))]

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
        st.subheader("📋 Listado - Pendientes de Pago (Tipo y Cantidad)")
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
        t_mostrar['Prima Neta'] = t_mostrar['Prima Neta'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(t_mostrar, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros bajo este criterio en el periodo actual.")

# -------------------------------------------------------------
# 2. BÚSQUEDA DE PÓLIZAS (SERIE, NOMBRE, PLACA)
# -------------------------------------------------------------
elif menu == "Búsqueda de Pólizas":
    st.header("🔍 Búsqueda Inteligente de Pólizas")
    criterio = st.text_input("Buscar por Nombre del Cliente, Serie del Auto o Placa:")
    
    if criterio:
        filtro = df[
            df['Cliente'].str.contains(criterio, case=False, na=False) |
            df['Serie'].str.contains(criterio, case=False, na=False) |
            df['Placa'].str.contains(criterio, case=False, na=False)
        ]
        if not filtro.empty:
            st.success(f"Se encontraron {len(filtro)} coincidencia(s):")
            st.dataframe(filtro[['Poliza', 'Cliente', 'Serie', 'Placa', 'Aseguradora', 'Vencimiento', 'Estatus_Poliza']], use_container_width=True, hide_index=True)
            
            # Botón para eliminar o quitar póliza
            pol_a_borrar = st.selectbox("Seleccione número de póliza a eliminar/quitar si es necesario:", filtro['Poliza'].tolist())
            if st.button("🗑️ Eliminar Póliza Seleccionada"):
                st.session_state.clientes = df[df['Poliza'] != pol_a_borrar].reset_index(drop=True)
                st.rerun()
        else:
            st.warning("No se encontraron registros con ese criterio.")

# -------------------------------------------------------------
# 3. REGISTRO Y RENOVACIÓN (CON AUTOCÁLCULOS Y RFC)
# -------------------------------------------------------------
elif menu == "Registro y Renovación":
    st.header("📝 Alta y Renovación de Póliza")
    
    with st.form("form_reg"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo del Cliente").upper()
            rfc = st.text_input("RFC (Calcula fecha de nacimiento automáticamente)").upper()
            
            # Autocálculo de fecha de nacimiento basada en RFC (ej: VELA851015...)
            nacimiento_auto = "1990-01-01"
            if len(rfc) >= 10:
                try:
                    anio_s = rfc[4:6]
                    mes_s = rfc[6:8]
                    dia_s = rfc[8:10]
                    sig = "19" if int(anio_s) > 30 else "20"
                    nacimiento_auto = f"{sig}{anio_s}-{mes_s}-{dia_s}"
                except:
                    pass
            
            nacimiento = st.date_input("Fecha de Nacimiento (Autocalculada por RFC)", value=pd.to_datetime(nacimiento_auto).date())
            telefono = st.text_input("Teléfono (10 dígitos)")
            
            # Correo con opciones sugeridas
            correo_usuario = st.text_input("Correo Electrónico")
            sugerencia_correo = st.selectbox("Sugerencia de Dominio", ["Personalizado", "@gmail.com", "@hotmail.com", "@yahoo.com"])
            correo = correo_usuario if sugerencia_correo == "Personalizado" else correo_usuario.split('@')[0] + sugerencia_correo

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
            forma_pago = st.selectbox("Forma de Pago", ["Contado", "Semestral", "Trimestral", "Mensual"])
            
            # Cálculo automático de vencimiento al ingresar emisión
            emision = st.date_input("Fecha de Emisión / Inicio")
            vigencia_anos = st.number_input("Vigencia (Años)", min_value=1, value=1)
            vencimiento_calculado = emision + timedelta(days=365 * vigencia_anos)
            vencimiento = st.date_input("Fecha de Vencimiento (Calculada Automática)", value=vencimiento_calculado)
            
            pago_limite = st.date_input("Fecha Límite de Pago")
            estatus_pago = st.selectbox("Estatus de Pago", ["Pendiente", "Pagada"])
            estatus_poliza = st.selectbox("Estatus de Póliza", ["Activa", "Cancelada"])
            mes_venta = st.selectbox("Mes de Contabilidad", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])

        submitted = st.form_submit_button("Guardar o Renovar Póliza")

        if submitted and nombre:
            # Sistema de detección de renovación: si la póliza ya existe, archiva la anterior
            if not df[df['Poliza'] == poliza].empty:
                anterior = df[df['Poliza'] == poliza]
                st.session_state.historico = pd.concat([st.session_state.historico, anterior], ignore_index=True)
                st.session_state.clientes = df[df['Poliza'] != poliza].reset_index(drop=True)
                st.info("🔄 Póliza anterior archivada en el respaldo histórico por renovación.")

            nuevo = {
                "Cliente": nombre, "RFC": rfc, "Telefono": telefono, "Correo": correo,
                "Nacimiento": str(nacimiento), "Contrato": contrato, "Poliza": poliza,
                "Serie": serie, "Placa": placa, "Aseguradora": aseguradora, "Vendedor": vendedor,
                "Ramo": ramo, "Uso_Auto": uso_auto, "Prima_Neta": prima_neta, "Forma_Pago": forma_pago,
                "Emision": str(emision), "Vencimiento": str(vencimiento), "Pago_Limite": str(pago_limite),
                "Estatus_Pago": estatus_pago, "Estatus_Poliza": estatus_poliza, "Mes_Venta": mes_venta
            }
            st.session_state.clientes = pd.concat([st.session_state.clientes, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("¡Póliza registrada y actualizada con éxito!")

# -------------------------------------------------------------
# 4. CENTRO DE COBRANZA & WHATSAPP
# -------------------------------------------------------------
elif menu == "Centro de Cobranza & WhatsApp":
    st.header("💬 Envío de Mensajes por WhatsApp (Pagos, Vencer, Renovar)")
    
    pendientes = df[df['Estatus_Pago'] == 'Pendiente']
    if not pendientes.empty:
        for idx, row in pendientes.iterrows():
            with st.expander(f"📌 {row['Cliente']} | Póliza: {row['Poliza']} ({row['Aseguradora']})"):
                st.write(f"**Uso:** {row['Uso_Auto']} | **Límite:** {row['Pago_Limite']} | **Prima Neta:** ${row['Prima_Neta']:,.2f}")
                msg = f"Hola {row['Cliente']}, le saludamos de Seguros Casa Pantera. Le recordamos que su póliza {row['Poliza']} ({row['Aseguradora']}) vence/requiere pago el {row['Pago_Limite']}. Quedamos a sus órdenes."
                link = f"https://wa.me/52{row['Telefono']}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#20B2AA; color:white; padding:8px 16px; border-radius:4px;">💬 Enviar WhatsApp de Cobranza</button></a>', unsafe_allow_html=True)
    else:
        st.success("No hay cobros pendientes.")

# -------------------------------------------------------------
# 5. AVISOS DE CUMPLEAÑOS
# -------------------------------------------------------------
elif menu == "Avisos de Cumpleaños":
    st.header("🎂 Avisos de Cumpleaños Automatizados")
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
# 6. REPORTE CONTABLE EN EXCEL (MENSUAL)
# -------------------------------------------------------------
elif menu == "Reporte Contable (Excel)":
    st.header("📈 Generación de Excel de Contabilidad Mensual")
    mes_rep = st.selectbox("Selecciona Mes Contable", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=9)
    
    df_rep = df[df['Mes_Venta'] == mes_rep]
    st.dataframe(df_rep[['Poliza', 'Cliente', 'Contrato', 'Aseguradora', 'Vendedor', 'Prima_Neta', 'Estatus_Pago', 'Estatus_Poliza']], use_container_width=True)
    
    if not df_rep.empty:
        total_m = df_rep['Prima_Neta'].sum()
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
