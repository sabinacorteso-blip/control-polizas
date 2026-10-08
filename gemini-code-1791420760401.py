import streamlit as st
import pandas as pd
from datetime import datetime
import io
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuración de la página
st.set_page_config(page_title="Control de Pólizas y Clientes", layout="wide")

# Simulación de base de datos inicial
if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame([
        {
            "Cliente": "María Rodríguez",
            "Telefono": "5512345678",
            "Correo": "maria@email.com",
            "Poliza": "POL-98765",
            "Aseguradora": "Quálitas",
            "Ramo": "Auto",
            "Prima": 12500.0,
            "Vencimiento": "2026-10-15",
            "Pago_Limite": "2026-10-10",
            "Renovacion": "2026-10-15",
            "Estatus_Pago": "Pendiente",
            "Mes_Venta": "Octubre"
        },
        {
            "Cliente": "Carlos Pérez",
            "Telefono": "5587654321",
            "Correo": "carlos@email.com",
            "Poliza": "POL-12345",
            "Aseguradora": "GNP",
            "Ramo": "Vida / PPR",
            "Prima": 25000.0,
            "Vencimiento": "2026-10-25",
            "Pago_Limite": "2026-10-25",
            "Renovacion": "2026-10-25",
            "Estatus_Pago": "Pagada",
            "Mes_Venta": "Octubre"
        }
    ])

st.title("Gestión Integral de Cartera y Ventas + Alertas")
st.markdown("---")

# Menú lateral
menu = st.sidebar.selectbox("Navegación", ["Dashboard del Mes", "Registro de Clientes y Pólizas", "Centro de Alertas", "Reporte de Ventas (Excel)"])

df = st.session_state.clientes
df['Vencimiento_dt'] = pd.to_datetime(df['Vencimiento'])

# -------------------------------------------------------------
# 1. DASHBOARD DEL MES
# -------------------------------------------------------------
if menu == "Dashboard del Mes":
    st.header("📊 Panel de Control - Mes Actual (Octubre 2026)")
    
    mes_actual = 10
    anio_actual = 2026
    df_mes = df[(df['Vencimiento_dt'].dt.month == mes_actual) & (df['Vencimiento_dt'].dt.year == anio_actual)]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Vencimientos del Mes", len(df_mes))
    col2.metric("Pólizas por Pagar / Pendientes", len(df_mes[df_mes['Estatus_Pago'] == 'Pendiente']))
    col3.metric("Renovaciones del Mes", len(df_mes))
    
    st.markdown("---")
    st.subheader("⚠️ Pólizas por Pagar / Vencer este Mes")
    if not df_mes.empty:
        st.dataframe(df_mes[['Cliente', 'Poliza', 'Aseguradora', 'Ramo', 'Pago_Limite', 'Estatus_Pago', 'Prima']], use_container_width=True)
    else:
        st.info("No hay registros que venzan en este mes.")

# -------------------------------------------------------------
# 2. REGISTRO DE CLIENTES Y PÓLIZAS
# -------------------------------------------------------------
elif menu == "Registro de Clientes y Pólizas":
    st.header("👥 Directorio de Clientes y Altas de Pólizas")
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Cliente")
            telefono = st.text_input("Teléfono (10 dígitos)")
            correo = st.text_input("Correo Electrónico")
            poliza = st.text_input("Número de Póliza")
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
                "Cliente": nombre,
                "Telefono": telefono,
                "Correo": correo,
                "Poliza": poliza,
                "Aseguradora": aseguradora,
                "Ramo": ramo,
                "Prima": prima,
                "Vencimiento": str(vencimiento),
                "Pago_Limite": str(pago_limite),
                "Renovacion": str(vencimiento),
                "Estatus_Pago": estatus,
                "Mes_Venta": mes_venta
            }
            st.session_state.clientes = pd.concat([st.session_state.clientes, pd.DataFrame([nuevo_registro])], ignore_index=True)
            st.success(f"¡Cliente {nombre} registrado con éxito!")
            
    st.markdown("---")
    st.dataframe(st.session_state.clientes[['Cliente', 'Telefono', 'Poliza', 'Aseguradora', 'Ramo', 'Prima', 'Vencimiento', 'Estatus_Pago']], use_container_width=True)

# -------------------------------------------------------------
# 3. CENTRO DE ALERTAS (WHATSAPP Y CORREO)
# -------------------------------------------------------------
elif menu == "Centro de Alertas":
    st.header("🔔 Centro de Alertas y Notificaciones")
    st.markdown("Genera mensajes automáticos para recordar pagos y vencimientos a tus clientes.")
    
    # Filtrar solo pólizas pendientes
    pendientes = df[df['Estatus_Pago'] == 'Pendiente']
    
    if pendientes.empty:
        st.success("¡Excelente! No hay pólizas pendientes de pago en este momento.")
    else:
        for index, row in pendientes.iterrows():
            with st.expander(f"📌 {row['Cliente']} - Póliza: {row['Poliza']} ({row['Aseguradora']})"):
                col_info, col_acciones = st.columns([2, 1])
                
                with col_info:
                    st.write(f"**Ramo:** {row['Ramo']}")
                    st.write(f"**Fecha Límite de Pago:** {row['Pago_Limite']}")
                    st.write(f"**Monto:** ${row['Prima']:,.2f}")
                    st.write(f"**Teléfono:** {row['Telefono']}")
                    st.write(f"**Correo:** {row['Correo']}")
                
                with col_acciones:
                    st.markdown("### Enviar Recordatorio")
                    
                    # 1. Alerta por WhatsApp (Enlace directo con mensaje prearmado)
                    mensaje_wa = f"Hola {row['Cliente']}, te saluda tu asesora. Te recuerdo que tu póliza {row['Poliza']} de {row['Aseguradora']} vence el próximo {row['Vencimiento']}. Quedo a tus órdenes para el apoyo con tu pago."
                    mensaje_wa_encoded = urllib.parse.quote(mensaje_wa)
                    link_wa = f"https://wa.me/52{row['Telefono']}?text={mensaje_wa_encoded}"
                    
                    st.markdown(f'<a href="{link_wa}" target="_blank"><button style="background-color:#25D366; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer; width:100%;">💬 Enviar WhatsApp</button></a>', unsafe_allow_html=True)
                    
                    # 2. Alerta por Correo Electrónico (Simulador / Envío SMTP opcional)
                    if st.button(f"✉️ Enviar Correo a {row['Cliente']}", key=f"mail_{index}"):
                        # Nota: Para envío real, configura tus credenciales SMTP aquí abajo o usa un servicio como SendGrid/Gmail
                        st.info(f"Correo simulado enviado con éxito a {row['Correo']} con los datos de cobro de la póliza {row['Poliza']}.")

# -------------------------------------------------------------
# 4. REPORTE DE VENTAS EN EXCEL
# -------------------------------------------------------------
elif menu == "Reporte de Ventas (Excel)":
    st.header("📈 Exportación de Ventas del Mes a Excel")
    
    mes_seleccionado = st.selectbox("Selecciona el mes a exportar", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=9)
    df_ventas = df[df['Mes_Venta'] == mes_seleccionado]
    
    st.subheader(f"Ventas registradas en: {mes_seleccionado}")
    st.dataframe(df_ventas[['Cliente', 'Poliza', 'Aseguradora', 'Ramo', 'Prima', 'Estatus_Pago']], use_container_width=True)
    
    if not df_ventas.empty:
        total_ventas = df_ventas['Prima'].sum()
        st.metric("Prima Total Vendida en el Mes", f"${total_ventas:,.2f}")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_ventas.to_excel(writer, index=False, sheet_name='Ventas')
        processed_data = output.getvalue()
        
        st.download_button(
            label=f"📥 Descargar Excel de Ventas - {mes_seleccionado}",
            data=processed_data,
            file_name=f"Ventas_{mes_seleccionado}_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No hay ventas registradas para este mes.")