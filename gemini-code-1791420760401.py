import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import urllib.parse

# Configuración de la página
st.set_page_config(page_title="Seguros Casa Pantera - Control de Cartera", layout="wide")

# Simulación de base de datos inicial con fechas relativas
hoy = datetime.now().date()

if "clientes" not in st.session_state:
    st.session_state.clientes = pd.DataFrame([
        {
            "Cliente": "RAFAEL MENDOZA MEDINA",
            "Telefono": "5512345678",
            "Correo": "rafael@email.com",
            "Nacimiento": "1985-10-15",
            "Poliza": "20275830",
            "Aseguradora": "QUÁLITAS",
            "Vendedor": "ANDRES",
            "Ramo": "Auto",
            "Prima_Neta": 4200.0,
            "Forma_Pago": "Trimestral",
            "Vencimiento": str(hoy + timedelta(days=3)),
            "Pago_Limite": str(hoy + timedelta(days=3)),
            "Estatus_Pago": "Pendiente",
            "Mes_Venta": "Octubre"
        },
        {
            "Cliente": "ALEJANDRO LARA SANCHEZ",
            "Telefono": "5587654321",
            "Correo": "alejandro@email.com",
            "Nacimiento": "1990-10-08",
            "Poliza": "20282485",
            "Aseguradora": "GNP",
            "Vendedor": "AXEL",
            "Ramo": "Vida / PPR",
            "Prima_Neta": 6000.0,
            "Forma_Pago": "Anual",
            "Vencimiento": str(hoy - timedelta(days=2)),
            "Pago_Limite": str(hoy - timedelta(days=2)),
            "Estatus_Pago": "Pendiente",
            "Mes_Venta": "Octubre"
        }
    ])

# -------------------------------------------------------------
# BARRA LATERAL CON LOGO Y NAVEGACIÓN
# -------------------------------------------------------------
with st.sidebar:
    # Inserta tu logo mediante enlace o imagen cargada
    st.image("https://images.unsplash.com/photo-1534188753412-3e26d0d618d6?q=80&w=300&auto=format&fit=crop", width=180) # O puedes usar la URL directa de tu logo si lo subes a GitHub
    st.markdown("## **SEGUROS CASA PANTERA**")
    st.markdown("---")
    menu = st.selectbox("Menú Principal", [
        "Dashboard del Mes", 
        "Registro de Clientes y Pólizas", 
        "Centro de Alertas & Cobranza", 
        "Avisos y Cumpleaños", 
        "Reporte de Ventas (Excel)"
    ])

df = st.session_state.clientes
df['Vencimiento_dt'] = pd.to_datetime(df['Vencimiento']).dt.date
df['Pago_Limite_dt'] = pd.to_datetime(df['Pago_Limite']).dt.date
df['Nacimiento_dt'] = pd.to_datetime(df['Nacimiento']).dt.date

# -------------------------------------------------------------
# 1. DASHBOARD DEL MES
# -------------------------------------------------------------
if menu == "Dashboard del Mes":
    st.header(f"📊 Panel de Control - Seguros Casa Pantera ({hoy.strftime('%B %Y')})")
    
    f_hoy = hoy
    pend_10d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] >= f_hoy) & (df['Pago_Limite_dt'] <= f_hoy + timedelta(days=10))]
    venc_5d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] < f_hoy) & (df['Pago_Limite_dt'] >= f_hoy - timedelta(days=5))]
    sin_pago_7d = df[(df['Estatus_Pago'] == 'Pendiente') & (df['Pago_Limite_dt'] < f_hoy - timedelta(days=1)) & (df['Pago_Limite_dt'] >= f_hoy - timedelta(days=7))]
    por_vencer_10d = df[(df['Vencimiento_dt'] >= f_hoy) & (df['Vencimiento_dt'] <= f_hoy + timedelta(days=10))]

    col1, col2, col3, col4 = st.columns(4)
    
    sel_metrica = "pendientes"
    if col1.button(f"🔔 Pendientes Pago (10d)\n\n **{len(pend_10d)}**", use_container_width=True):
        sel_metrica = "pendientes"
    if col2.button(f"⚠️ Pagos Vencidos (5d)\n\n **{len(venc_5d)}**", use_container_width=True):
        sel_metrica = "vencidos"
    if col3.button(f"❌ Sin Pago (1-7d)\n\n **{len(sin_pago_7d)}**", use_container_width=True):
        sel_metrica = "sin_pago"
    if col4.button(f"📅 Próx. Vencer (10d)\n\n **{len(por_vencer_10d)}**", use_container_width=True):
        sel_metrica = "vencer"

    st.markdown("---")

    if sel_metrica == "pendientes":
        st.subheader("📋 Listado - Pendientes de Pago (10 días)")
        data_mostrar = pend_10d
    elif sel_metrica == "vencidos":
        st.subheader("📋 Listado - Pagos Vencidos (Últimos 5 días)")
        data_mostrar = venc_5d
    elif sel_metrica == "sin_pago":
        st.subheader("📋 Listado - Sin Pago (1 a 7 días)")
        data_mostrar = sin_pago_7d
    elif sel_metrica == "vencer":
        st.subheader("📋 Listado - Pólizas por Vencer (10 días)")
        data_mostrar = por_vencer_10d

    if not data_mostrar.empty:
        tabla_estilizada = data_mostrar[['Poliza', 'Cliente', 'Aseguradora', 'Vendedor', 'Prima_Neta', 'Pago_Limite']].copy()
        tabla_estilizada.columns = ['Folio', 'Cliente', 'Aseguradora', 'Vendedor', 'Prima Neta', 'Fecha Límite']
        tabla_estilizada['Prima Neta'] = tabla_estilizada['Prima Neta'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(tabla_estilizada, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros en este criterio.")

# -------------------------------------------------------------
# 2. REGISTRO DE CLIENTES Y PÓLIZAS
# -------------------------------------------------------------
elif menu == "Registro de Clientes y Pólizas":
    st.header("👥 Alta de Clientes y Pólizas - Seguros Casa Pantera")
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre Completo del Cliente (MAYÚSCULAS)")
            telefono = st.text_input("Teléfono (10 dígitos)")
            correo = st.text_input("Correo Electrónico")
            nacimiento = st.date_input("Fecha de Nacimiento (Cumpleaños)")
            poliza = st.text_input("Número de Póliza / Folio")
            
            # Aseguradoras solicitadas + Otro
            aseguradora_op = ["ANA", "AFIRME", "QUÁLITAS", "GENERAL DE SEGUROS", "BANORTE", "GNP", "OTRO"]
            aseguradora_sel = st.selectbox("Aseguradora", aseguradora_op)
            aseguradora = st.text_input("Especifique aseguradora (si eligió OTRO)") if aseguradora_sel == "OTRO" else aseguradora_sel

        with col2:
            # Vendedores solicitados + Otro
            vendedor_op = ["ANDRES", "AXEL", "OTRO"]
            vendedor_sel = st.selectbox("Asesor / Vendedor", vendedor_op)
            vendedor = st.text_input("Especifique nombre del asesor (si eligió OTRO)") if vendedor_sel == "OTRO" else vendedor_sel

            ramo = st.selectbox("Ramo", ["Auto", "Vida / PPR", "Gastos Médicos Mayores", "Daños", "Accidentes"])
            prima_neta = st.number_input("Monto Prima Neta ($)", min_value=0.0, format="%.2f")
            forma_pago = st.selectbox("Forma de Pago / Fraccionamiento", ["Contado", "Semestral", "Trimestral", "Mensual"])
            vencimiento = st.date_input("Fecha de Vencimiento de Póliza")
            pago_limite = st.date_input("Fecha Límite de Pago / Recibo")
            estatus = st.selectbox("Estatus de Pago", ["Pendiente", "Pagada"])
            mes_venta = st.selectbox("Mes de Venta", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            
        submitted = st.form_submit_button("Guardar Registro en Cartera")
        
        if submitted and nombre:
            nuevo_registro = {
                "Cliente": nombre.upper(),
                "Telefono": telefono,
                "Correo": correo,
                "Nacimiento": str(nacimiento),
                "Poliza": poliza,
                "Aseguradora": aseguradora,
                "Vendedor": vendedor,
                "Ramo": ramo,
                "Prima_Neta": prima_neta,
                "Forma_Pago": forma_pago,
                "Vencimiento": str(vencimiento),
                "Pago_Limite": str(pago_limite),
                "Estatus_Pago": estatus,
                "Mes_Venta": mes_venta
            }
            st.session_state.clientes = pd.concat([st.session_state.clientes, pd.DataFrame([nuevo_registro])], ignore_index=True)
            st.success(f"¡Cliente {nombre} registrado con éxito en Seguros Casa Pantera!")
            
    st.markdown("---")
    st.subheader("Directorio General de Cartera")
    st.dataframe(st.session_state.clientes[['Cliente', 'Poliza', 'Aseguradora', 'Vendedor', 'Prima_Neta', 'Forma_Pago', 'Estatus_Pago']], use_container_width=True)

# -------------------------------------------------------------
# 3. CENTRO DE ALERTAS & COBRANZA
# -------------------------------------------------------------
elif menu == "Centro de Alertas & Cobranza":
    st.header("🔔 Centro de Control de Cobranza y Recordatorios de Pago")
    st.markdown("Gestión de pagos fraccionados y alertas directas por WhatsApp.")
    
    pendientes = df[df['Estatus_Pago'] == 'Pendiente']
    
    if pendientes.empty:
        st.success("¡Excelente! No hay cobranza pendiente en este momento.")
    else:
        for index, row in pendientes.iterrows():
            with st.expander(f"📌 {row['Cliente']} | Póliza: {row['Poliza']} ({row['Aseguradora']}) - Vendedor: {row['Vendedor']}"):
                col_i, col_a = st.columns([2, 1])
                with col_i:
                    st.write(f"**Ramo:** {row['Ramo']}")
                    st.write(f"**Forma de Pago:** {row['Forma_Pago']}")
                    st.write(f"**Fecha Límite de Cobro:** {row['Pago_Limite']}")
                    st.write(f"**Prima Neta:** ${row['Prima_Neta']:,.2f}")
                    st.write(f"**Teléfono:** {row['Telefono']}")
                with col_a:
                    mensaje_wa = f"Hola {row['Cliente']}, le saludamos de Seguros Casa Pantera. Le recordamos que su recibo/póliza {row['Poliza']} ({row['Aseguradora']}) con forma de pago {row['Forma_Pago']} tiene fecha límite el {row['Pago_Limite']}. Quedamos a sus órdenes para apoyar con su trámite."
                    link_wa = f"https://wa.me/52{row['Telefono']}?text={urllib.parse.quote(mensaje_wa)}"
                    st.markdown(f'<a href="{link_wa}" target="_blank"><button style="background-color:#25D366; color:white; padding:10px 16px; border:none; border-radius:4px; cursor:pointer; width:100%;">💬 Cobranza WhatsApp</button></a>', unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. AVISOS Y CUMPLEAÑOS AUTOMATIZADOS
# -------------------------------------------------------------
elif menu == "Avisos y Cumpleaños":
    st.header("🎂 Avisos de Cumpleaños y Felicitación Automatizada")
    st.markdown("Clientes que cumplen años en el mes actual:")
    
    mes_actual_num = hoy.month
    df['Mes_Cumple'] = pd.to_datetime(df['Nacimiento']).dt.month
    cumpleañeros = df[df['Mes_Cumple'] == mes_actual_num]
    
    if not cumpleañeros.empty:
        for idx, row in cumpleañeros.iterrows():
            with st.container():
                col_c1, col_c2 = st.columns([3, 1])
                with col_c1:
                    st.write(f"🎈 **{row['Cliente']}** — Fecha de Nacimiento: {row['Nacimiento']} — Tel: {row['Telefono']}")
                with col_c2:
                    msg_cumple = f"¡Muchas felicidades en tu cumpleaños de parte de todo el equipo de Seguros Casa Pantera! 🥳 Te deseamos un excelente día rodeado de tus seres queridos."
                    link_cumple = f"https://wa.me/52{row['Telefono']}?text={urllib.parse.quote(msg_cumple)}"
                    st.markdown(f'<a href="{link_cumple}" target="_blank"><button style="background-color:#007bff; color:white; padding:6px 12px; border:none; border-radius:4px; cursor:pointer;">🎁 Enviar Felicitación</button></a>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No hay registros de cumpleaños para este mes.")

# -------------------------------------------------------------
# 5. REPORTE DE VENTAS EN EXCEL
# -------------------------------------------------------------
elif menu == "Reporte de Ventas (Excel)":
    st.header("📈 Exportación de Ventas y Prima Neta a Excel")
    
    mes_seleccionado = st.selectbox("Selecciona el mes a exportar", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=9)
    df_ventas = df[df['Mes_Venta'] == mes_seleccionado]
    
    st.dataframe(df_ventas[['Cliente', 'Poliza', 'Aseguradora', 'Vendedor', 'Ramo', 'Prima_Neta', 'Forma_Pago', 'Estatus_Pago']], use_container_width=True)
    
    if not df_ventas.empty:
        total_prima_neta = df_ventas['Prima_Neta'].sum()
        st.metric("Prima Neta Total Vendida en el Mes", f"${total_prima_neta:,.2f}")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_ventas.to_excel(writer, index=False, sheet_name='Ventas_Casa_Pantera')
        
        st.download_button(
            label=f"📥 Descargar Excel de Ventas - {mes_seleccionado}",
            data=output.getvalue(),
            file_name=f"Ventas_Casa_Pantera_{mes_seleccionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No hay ventas registradas en este mes.")
