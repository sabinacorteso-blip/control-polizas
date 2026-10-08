import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import urllib.parse

# Configuración de la página
st.set_page_config(page_title="Control de Pólizas y Clientes", layout="wide")

# Simulación de base de datos inicial con fechas relativas a hoy para probar los filtros
hoy = datetime.now().date()

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame([
        {
            "Cliente": "RAFAEL MENDOZA MEDINA",
            "Telefono": "5512345678",
            "Correo": "rafael@email.com",
            "Poliza": "20275830",
            "Aseguradora": "Quálitas",
            "Ramo": "Auto",
            "Prima": 4576.0,
            "Vencimiento": str(hoy + timedelta(days=3)),
            "Pago_Limite": str(hoy + timedelta(days=3)),
            "Estatus_Pago": "Pendiente",
            "Mes_Venta": "Octubre"
        },
        {
            "Cliente": "ALEJANDRO LARA SANCHEZ",
            "Telefono": "5587654321",
            "Correo": "alejandro@email.com",
            "Poliza": "20282485",
            "Aseguradora": "GNP",
            "Ramo": "Vida / PPR",
            "Prima": 6420.0,
            "Vencimiento": str(hoy - timedelta(days=2)),
            "Pago_Limite": str(hoy - timedelta(days=2)),
            "Estatus_Pago": "Pendiente",
            "Mes_Venta": "Octubre"
        },
        {
            "Cliente": "JULIO CESAR MORA MUÑOZ",
            "Telefono": "5599887766",
            "Correo": "julio@email.com",
            "Poliza": "20282685",
            "Aseguradora": "AXA",
            "Ramo": "Gastos Médicos",
            "Prima": 6420.0,
            "Vencimiento": str(hoy + timedelta(days=8)),
            "Pago_Limite": str(hoy + timedelta(days=8)),
            "Estatus_Pago": "Pendiente",
            "Mes_Venta": "Octubre"
        }
    ])

st.title("Gestión Integral de Cartera y Ventas")
st.markdown("---")

# Menú lateral
menu = st.sidebar.selectbox("Navegación", ["Dashboard del Mes", "Registro de Clientes y Pólizas", "Centro de Alertas", "Reporte de Ventas (Excel)"])

df = st.session_state.clientes
df['Vencimiento_dt'] = pd.to_datetime(df['Vencimiento']).dt.date
df['Pago_Limite_dt'] = pd.to_datetime(df['Pago_Limite']).dt.date

# -------------------------------------------------------------
# 1. DASHBOARD DEL MES (CON MÉTRICAS Y FILTROS EXACTOS)
# -------------------------------------------------------------
if menu == "Dashboard del Mes":
    st.header(f"📊 Panel de Control - Monitoreo de Cartera ({hoy.strftime('%B %Y')})")
    
    # Cálculo de rangos de fechas respecto a hoy
    f_hoy = hoy
    
    # 1. Pendientes de Pago (próximos 10 días)
    pend_10d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] >= f_hoy) & (df['Pago_Limite_dt'] <= f_hoy + timedelta(days=10))]
    
    # 2. Pagos Vencidos (últimos 5 días)
    venc_5d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] < f_hoy) & (df['Pago_Limite_dt'] >= f_hoy - timedelta(days=5))]
    
    # 3. Sin pago (1 a 7 días)
    sin_pago_7d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] < f_hoy - timedelta(days=1)) & (df['Pago_Limite_dt'] >= f_hoy - timedelta(days=7))]
    
    # 4. Pólizas por Vencer (próximos 10 días)
    por_vencer_10d = df[(df['Vencimiento_dt'] >= f_hoy) & (df['Vencimiento_dt'] <= f_hoy + timedelta(days=10))]

    # Mostrar métricas en columnas interactivas
    col1, col2, col3, col4 = st.columns(4)
    
    sel_metrica = None
    if col1.button(f"🔔 Pendientes Pago (10d)\n\n **{len(pend_10d)}**"):
        sel_metrica = "pendientes"
    if col2.button(f"⚠️ Pagos Vencidos (5d)\n\n **{len(venc_5d)}**"):
        sel_metrica = "vencidos"
    if col3.button(f"❌ Sin Pago (1-7d)\n\n **{len(sin_pago_7d)}**"):
        sel_metrica = "sin_pago"
    if col4.button(f"📅 Próx. Vencer (10d)\n\n **{len(por_vencer_10d)}**"):
        sel_metrica = "vencer"

    st.markdown("---")

    # Mostrar despliegue detallado según la tarjeta seleccionada (similares a la ventana modal solicitada)
    if sel_metrica == "pendientes" or 'vista_activa' not in st.session_state:
        st.subheader("📋 Listado de Pólizas - Pendientes de Pago (Próximos 10 días)")
        data_mostrar = pend_10d
    elif sel_metrica == "vencidos":
        st.subheader("📋 Listado de Pólizas - Pagos Vencidos (Últimos 5 días)")
        data_mostrar = venc_5d
    elif sel_metrica == "sin_pago":
        st.subheader("📋 Listado de Pólizas - Sin Pago (1 a 7 días)")
        data_mostrar = sin_pago_7d
    elif sel_metrica == "vencer":
        st.subheader("📋 Listado de Pólizas - Pólizas por Vencer (Próximos 10 días)")
        data_mostrar = por_vencer_10d

    if not data_mostrar.empty:
        # Formato visual limpio idéntico al solicitado
        tabla_estilizada = data_mostrar[['Poliza', 'Cliente', 'Prima', 'Pago_Limite']].copy()
        tabla_estilizada.columns = ['Folio', 'Cliente', 'Total', 'Fecha']
        tabla_estilizada['Total'] = tabla_estilizada['Total'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(tabla_estilizada, use_container_width=True, hide_index=True)
    else:
        st.info("No hay pólizas en este criterio para el periodo seleccionado.")

# -------------------------------------------------------------
# 2. REGISTRO DE CLIENTES Y PÓLIZAS
# -------------------------------------------------------------
elif menu == "Registro de Clientes y Pólizas":
    st.header("👥 Directorio de Clientes y Altas de Pólizas")
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Cliente (MAYÚSCULAS)")
            telefono = st.text_input("Teléfono (10 dígitos)")
            correo = st.text_input("Correo Electrónico")
            poliza = st.text_input("Número de Póliza / Folio")
            aseguradora = st.selectbox("Aseguradora", ["GNP", "Quálitas", "A.N.A. Seguros", "AXA", "Zurich", "MetLife", "Otro"])
        
        with col2:
            ramo = st.selectbox("Ramo", ["Auto", "Vida / PPR", "Gastos Médicos Mayores", "Daños", "Accidentes"])
            prima = st.number_input("Monto de la Prima ($)", min_value=0.0, format="%.2f")
            vencimiento = st.date_input("Fecha de Vencimiento")
            pago_limite = st.date_input("Fecha Límite de Pago")
            estatus = st.selectbox("Estatus de Pago", ["Pendiente", "Pagada"])
            mes_venta = st.selectbox("Mes de Venta", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            
        submitted = st.form_submit_button("Guardar Registro")
        
        if submitted and nombre:
            nuevo_registro = {
                "Cliente": nombre.upper(),
                "Telefono": telefono,
                "Correo": correo,
                "Poliza": poliza,
                "Aseguradora": aseguradora,
                "Ramo": ramo,
                "Prima": prima,
                "Vencimiento": str(vencimiento),
                "Pago_Limite": str(pago_limite),
                "Estatus_Pago": estatus,
                "Mes_Venta": mes_venta
            }
            st.session_state.clientes = pd.concat([st.session_state.clientes, pd.DataFrame([nuevo_registro])], ignore_index=True)
            st.success(f"¡Cliente {nombre} registrado con éxito!")
            
    st.markdown("---")
    st.subheader("Base de Datos General")
    st.dataframe(st.session_state.clientes[['Cliente', 'Poliza', 'Aseguradora', 'Ramo', 'Prima', 'Pago_Limite', 'Estatus_Pago']], use_container_width=True)

# -------------------------------------------------------------
# 3. CENTRO DE ALERTAS
# -------------------------------------------------------------
elif menu == "Centro de Alertas":
    st.header("🔔 Centro de Alertas por WhatsApp")
    pendientes = df[df['Estatus_Pago'] == 'Pendiente']
    
    if pendientes.empty:
        st.success("¡Excelente! No hay pólizas pendientes de pago.")
    else:
        for index, row in pendientes.iterrows():
            with st.expander(f"📌 {row['Cliente']} - Póliza: {row['Poliza']} ({row['Aseguradora']})"):
                st.write(f"**Fecha Límite:** {row['Pago_Limite']} | **Monto:** ${row['Prima']:,.2f}")
                mensaje_wa = f"Hola {row['Cliente']}, te recuerdo que tu póliza {row['Poliza']} de {row['Aseguradora']} tiene fecha límite de pago el {row['Pago_Limite']}. Quedo a tus órdenes."
                link_wa = f"https://wa.me/52{row['Telefono']}?text={urllib.parse.quote(mensaje_wa)}"
                st.markdown(f'<a href="{link_wa}" target="_blank"><button style="background-color:#25D366; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer;">💬 Enviar WhatsApp</button></a>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. REPORTE DE VENTAS EN EXCEL
# -------------------------------------------------------------
elif menu == "Reporte de Ventas (Excel)":
    st.header("📈 Exportación de Ventas del Mes a Excel")
    mes_seleccionado = st.selectbox("Selecciona el mes a exportar", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=9)
    df_ventas = df[df['Mes_Venta'] == mes_seleccionado]
    
    st.dataframe(df_ventas[['Cliente', 'Poliza', 'Aseguradora', 'Ramo', 'Prima', 'Estatus_Pago']], use_container_width=True)
    
    if not df_ventas.empty:
        total_ventas = df_ventas['Prima'].sum()
        st.metric("Prima Total Vendida en el Mes", f"${total_ventas:,.2f}")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_ventas.to_excel(writer, index=False, sheet_name='Ventas')
        
        st.download_button(
            label=f"📥 Descargar Excel de Ventas - {mes_seleccionado}",
            data=output.getvalue(),
            file_name=f"Ventas_{mes_seleccionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
