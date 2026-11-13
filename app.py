"""
BancoVigía · Monitoreo Integral de Clientes y Operaciones
Aplicativo interactivo en Streamlit conectado a SQL Server (Grupo 8 · Ingeniería de Datos).

Ejecutar:  streamlit run app.py
"""
import datetime as dt
import os

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import reportes as rp
from consultas_misiones import CONSULTAS, MISIONES
from db import BaseDatos, drivers_disponibles

BASE = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(page_title="BancoVigía · Monitoreo 360°", page_icon="🏦", layout="wide")

st.markdown("""
<style>
    .block-container {padding-top: 1.6rem;}
    div[data-testid="stMetric"] {background: #F4F7FB; border: 1px solid #E1E8F0;
        border-radius: 10px; padding: 10px 14px;}
    div[data-testid="stMetricLabel"] p {color: #1F3864; font-weight: 600;}
    .chip {display:inline-block; background:#E8EEF7; color:#1F3864; border-radius:12px;
        padding:2px 10px; margin:2px 4px 2px 0; font-size:0.85rem;}
    .nota {color:#666; font-size:0.85rem;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Conexión
# ---------------------------------------------------------------------------
def conectar(modo, servidor, driver, usuario, clave):
    try:
        st.session_state.db = BaseDatos(modo, servidor=servidor, driver=driver, usuario=usuario, clave=clave)
        st.session_state.error_conexion = None
    except Exception as e:  # si SQL Server no responde se usa la base demo
        st.session_state.error_conexion = str(e)
        st.session_state.db = BaseDatos("demo")


EN_LINEA = not drivers_disponibles()   # en Streamlit Cloud no hay drivers ODBC ni SQL Server

if "db" not in st.session_state:
    if EN_LINEA:
        st.session_state.db = BaseDatos("demo")
        st.session_state.error_conexion = None
    else:
        conectar("sqlserver", os.environ.get("BANCOVIGIA_SERVER", "localhost"), None, None, None)

with st.sidebar:
    st.markdown("## 🏦 BancoVigía")
    st.caption("Monitoreo integral de clientes y operaciones")
    pagina = st.radio(
        "Navegación",
        ["Resumen ejecutivo", "Monitoreo de fraude", "Equipo de riesgo", "Perfil 360° del cliente",
         "Cartera y atención", "Consultas SQL (misiones)", "Modelo de datos"],
        label_visibility="collapsed",
    )
    st.divider()
    with st.expander("⚙️ Conexión a la base de datos",
                     expanded=st.session_state.get("error_conexion") is not None):
        modo = st.radio("Origen de datos", ["SQL Server", "Demo (SQLite)"], horizontal=True)
        servidor = st.text_input("Servidor", value=os.environ.get("BANCOVIGIA_SERVER", "localhost"),
                                 help=r"Ejemplos: localhost, .\SQLEXPRESS, NOMBRE-PC\SQLEXPRESS")
        drivers = drivers_disponibles() or ["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server"]
        driver = st.selectbox("Driver ODBC", drivers, index=len(drivers) - 1)
        autenticacion = st.radio("Autenticación", ["Windows", "Usuario SQL"], horizontal=True)
        usuario = clave = None
        if autenticacion == "Usuario SQL":
            usuario = st.text_input("Usuario", value="sa")
            clave = st.text_input("Contraseña", type="password")
        if st.button("Conectar", type="primary"):
            conectar("sqlserver" if modo == "SQL Server" else "demo", servidor, driver, usuario, clave)
            st.cache_data.clear()

    db = st.session_state.db
    if db.modo == "sqlserver":
        st.success(f"Conectado: {db.descripcion}")
    elif EN_LINEA:
        st.info("Versión en línea · datos de demostración (los mismos de la base SQL Server)")
    else:
        st.info(db.descripcion)
        if st.session_state.get("error_conexion"):
            st.caption("No se pudo conectar a SQL Server; se muestran los datos de la base demo.")


# ---------------------------------------------------------------------------
# Carga de datos (desde las vistas de SQL Server)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Consultando la base de datos…")
def leer(_db, origen, sql):
    return _db.consultar(sql)


CLAVE = db.descripcion
td_all = leer(db, CLAVE, "SELECT * FROM dbo.vw_TransaccionDetalle")
inv_all = leer(db, CLAVE, "SELECT * FROM dbo.vw_InvestigacionDetalle")


def soles(x):
    return f"S/ {x:,.0f}"


def mostrar(fig):
    st.pyplot(fig)
    plt.close(fig)


def descargar(df, nombre, etiqueta="⬇️ Descargar CSV"):
    st.download_button(etiqueta, df.to_csv(index=False).encode("utf-8-sig"), file_name=nombre,
                       mime="text/csv")


def rango_fechas(etiqueta, minimo, maximo, clave):
    valor = st.date_input(etiqueta, value=(minimo, maximo), min_value=minimo, max_value=maximo, key=clave)
    if isinstance(valor, (tuple, list)) and len(valor) == 2:
        return pd.Timestamp(valor[0]), pd.Timestamp(valor[1])
    inicio = valor[0] if isinstance(valor, (tuple, list)) else valor
    return pd.Timestamp(inicio), pd.Timestamp(maximo)


# ---------------------------------------------------------------------------
# Página 1: Resumen ejecutivo
# ---------------------------------------------------------------------------
def pagina_resumen():
    st.title("Resumen ejecutivo de operaciones")
    st.caption("Fuente: dbo.vw_TransaccionDetalle y dbo.vw_InvestigacionDetalle")

    f1, f2, f3 = st.columns([1.4, 1, 1.4])
    with f1:
        ini, fin = rango_fechas("Rango de fechas", td_all["TransactionDate"].min().date(),
                                td_all["TransactionDate"].max().date(), "res_fechas")
    with f2:
        cuentas = st.multiselect("Tipo de cuenta", ["Current", "Savings"], default=["Current", "Savings"],
                                 format_func=lambda c: {"Current": "Corriente", "Savings": "Ahorros"}[c])
    with f3:
        ciudades = st.multiselect("Ciudad de la sucursal", sorted(td_all["BranchCity"].unique()),
                                  placeholder="Todas las ciudades")

    td = td_all[td_all["TransactionDate"].between(ini, fin) & td_all["AccountType"].isin(cuentas)]
    if ciudades:
        td = td[td["BranchCity"].isin(ciudades)]
    inv = inv_all[inv_all["TransactionID"].isin(td["TransactionID"])]
    vig = inv[inv["EsDictamenVigente"] == 1]

    k = st.columns(6)
    k[0].metric("Transacciones", f"{len(td):,}")
    k[1].metric("Monto transaccionado", soles(td["TransactionAmount"].sum()))
    k[2].metric("Clientes activos", f"{td['CustomerID'].nunique():,}")
    pct = (td["Anomaly"] == -1).mean() if len(td) else 0
    k[3].metric("Alertas antifraude", f"{(td['Anomaly'] == -1).sum():,}", f"{pct:.1%} del total",
                delta_color="off")
    k[4].metric("Casos sin cerrar", f"{(vig['Verdict'] == 'Under Review').sum():,}")
    k[5].metric("Fraudes confirmados", f"{(vig['Verdict'] == 'Fraud Confirmed').sum():,}",
                soles(vig.loc[vig['Verdict'] == 'Fraud Confirmed', 'TransactionAmount'].sum()),
                delta_color="off")

    mostrar(rp.fig_tendencia_mensual(td))
    c1, c2 = st.columns([1.5, 1])
    with c1:
        mostrar(rp.fig_tipo_transaccion(td))
    with c2:
        mostrar(rp.fig_cuentas(td))

    with st.expander("Ver el detalle de transacciones filtradas"):
        st.dataframe(td, hide_index=True)
        descargar(td, "transacciones_filtradas.csv")


# ---------------------------------------------------------------------------
# Página 2: Monitoreo de fraude
# ---------------------------------------------------------------------------
def pagina_fraude():
    st.title("Monitoreo de fraude")
    st.caption("Transacciones marcadas por el sistema antifraude (Anomaly = -1) y su investigación")

    f1, f2, f3 = st.columns([1.4, 1.2, 1])
    with f1:
        ciudades = st.multiselect("Ciudad de la sucursal", sorted(td_all["BranchCity"].unique()),
                                  placeholder="Todas las ciudades", key="fr_ciudad")
    with f2:
        tipos = st.multiselect("Tipo de operación", ["Deposit", "Withdrawal", "Transfer"],
                               default=["Deposit", "Withdrawal", "Transfer"],
                               format_func=lambda t: rp.ETIQUETA_TIPO[t])
    with f3:
        monto_min = st.slider("Monto mínimo (S/)", 0, 5000, 0, step=250)

    td = td_all[td_all["TransactionType"].isin(tipos) & (td_all["TransactionAmount"] >= monto_min)]
    if ciudades:
        td = td[td["BranchCity"].isin(ciudades)]
    an = td[td["Anomaly"] == -1]
    inv = inv_all[inv_all["TransactionID"].isin(an["TransactionID"])]
    vig = inv[inv["EsDictamenVigente"] == 1]

    k = st.columns(4)
    k[0].metric("Transacciones anómalas", f"{len(an):,}")
    k[1].metric("Monto en riesgo", soles(an["TransactionAmount"].sum()))
    k[2].metric("Casos en revisión", f"{(vig['Verdict'] == 'Under Review').sum():,}")
    tasa = (vig["Verdict"] == "Fraud Confirmed").mean() if len(vig) else 0
    k[3].metric("Tasa de fraude confirmado", f"{tasa:.1%}")

    c1, c2 = st.columns(2)
    with c1:
        mostrar(rp.fig_anomalias_ciudad(td))
    with c2:
        mostrar(rp.fig_heatmap_ciudad_trimestre(td))

    # Severidad calculada en SQL Server con la función escalar dbo.fn_SeveridadFraude
    sev = leer(db, CLAVE, """
        SELECT TransactionID, BranchCity, Analista, TransactionDate, TransactionType,
               TransactionAmount, Verdict,
               dbo.fn_SeveridadFraude(Verdict, TransactionAmount) AS Severidad
        FROM dbo.vw_InvestigacionDetalle
        WHERE EsDictamenVigente = 1""")
    sev = sev[sev["TransactionID"].isin(an["TransactionID"])]

    c3, c4 = st.columns(2)
    with c3:
        mostrar(rp.fig_dictamenes(inv))
    with c4:
        mostrar(rp.fig_severidad(sev))

    st.subheader("Casos priorizados por severidad")
    niveles = st.multiselect("Nivel de severidad", ["Crítico", "Alto", "Medio", "Bajo"],
                             default=["Crítico", "Alto"])
    tabla = (sev[sev["Severidad"].isin(niveles)]
             .sort_values(["Severidad", "TransactionAmount"], ascending=[True, False])
             .assign(Verdict=lambda d: d["Verdict"].map(rp.ETIQUETA_DICTAMEN)))
    st.dataframe(tabla, hide_index=True,
                 column_config={"TransactionAmount": st.column_config.NumberColumn("Monto", format="S/ %.2f"),
                                "TransactionDate": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")})
    descargar(tabla, "casos_priorizados.csv")


# ---------------------------------------------------------------------------
# Página 3: Equipo de riesgo
# ---------------------------------------------------------------------------
def pagina_equipo():
    st.title("Equipo de analistas de riesgo")
    st.caption("Productividad calculada por el procedimiento almacenado dbo.sp_DesempenoAnalistas")

    sucursales = leer(db, CLAVE, """
        SELECT DISTINCT B.BranchID, B.BranchName
        FROM dbo.Analyst AS A JOIN dbo.Branch AS B ON B.BranchID = A.BranchID
        ORDER BY B.BranchID""")
    opciones = [None] + sucursales["BranchID"].tolist()
    nombres = dict(zip(sucursales["BranchID"], sucursales["BranchName"]))

    with st.form("form_sp"):
        c1, c2, c3, c4 = st.columns(4)
        fi = c1.date_input("Desde", dt.date(2023, 1, 1))
        ff = c2.date_input("Hasta", dt.date(2023, 12, 31))
        suc = c3.selectbox("Sucursal", opciones,
                           format_func=lambda b: "Todas" if b is None else f"{b} · {nombres[b]}")
        ver = c4.selectbox("Dictamen", [None, "Fraud Confirmed", "False Positive", "Under Review"],
                           format_func=lambda v: "Todos" if v is None else rp.ETIQUETA_DICTAMEN[v])
        st.form_submit_button("Ejecutar procedimiento", type="primary")

    st.code(f"EXEC dbo.sp_DesempenoAnalistas @FechaInicio = '{fi}', @FechaFin = '{ff}', "
            f"@BranchID = {suc if suc is not None else 'NULL'}, "
            f"@Verdict = {repr(ver) if ver else 'NULL'};", language="sql")

    res = db.sp_desempeno_analistas(fi, ff, suc, ver)
    if res is None or res.empty:
        st.warning("No hay investigaciones para los filtros indicados (validación IF del procedimiento).")
    else:
        k = st.columns(4)
        k[0].metric("Analistas con casos", len(res))
        k[1].metric("Casos asignados", int(res["CasosAsignados"].sum()))
        k[2].metric("Monto investigado", soles(res["MontoInvestigado"].sum()))
        cerr = 1 - res["EnRevision"].sum() / res["CasosAsignados"].sum()
        k[3].metric("Casos cerrados", f"{cerr:.1%}")
        c1, c2 = st.columns([1.35, 1])
        with c1:
            mostrar(rp.fig_desempeno(res))
        with c2:
            mostrar(rp.fig_tiempo_respuesta(res))
        st.dataframe(res, hide_index=True)
        descargar(res, "desempeno_analistas.csv")

    st.subheader("Jerarquía de supervisión (relación recursiva Analyst → Analyst)")
    jer = leer(db, CLAVE, """
        SELECT A.AnalystID, A.AnalystFirstName + ' ' + A.AnalystLastName AS Analista,
               A.SupervisorID, B.BranchName
        FROM dbo.Analyst AS A JOIN dbo.Branch AS B ON B.BranchID = A.BranchID""") \
        if db.modo == "sqlserver" else leer(db, CLAVE, """
        SELECT A.AnalystID, A.AnalystFirstName || ' ' || A.AnalystLastName AS Analista,
               A.SupervisorID, B.BranchName
        FROM Analyst A JOIN Branch B ON B.BranchID = A.BranchID""")
    con_casos = set(inv_all["AnalystID"])
    lineas = ['digraph G { rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=10];']
    for _, r in jer.iterrows():
        es_sup = r["AnalystID"] in set(jer["SupervisorID"].dropna().astype(int))
        color = "#1F3864" if es_sup else ("#DCE6F2" if r["AnalystID"] in con_casos else "#F9D9D6")
        fuente = "white" if es_sup else "black"
        lineas.append(f'n{r.AnalystID} [label="{r.Analista}\\n{r.BranchName}", fillcolor="{color}", '
                      f'fontcolor="{fuente}"];')
        if pd.notna(r["SupervisorID"]):
            lineas.append(f"n{int(r.SupervisorID)} -> n{r.AnalystID};")
    lineas.append("}")
    st.graphviz_chart("\n".join(lineas))
    st.markdown('<span class="nota">Azul oscuro: supervisores · celeste: analistas con casos · '
                'rosado: analistas sin casos asignados</span>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Página 4: Perfil 360° del cliente
# ---------------------------------------------------------------------------
def pagina_perfil():
    st.title("Perfil 360° del cliente")
    st.caption("Resultado del procedimiento almacenado dbo.sp_PerfilCliente360 y la vista dbo.vw_PerfilCliente360")

    perfil = leer(db, CLAVE, "SELECT * FROM dbo.vw_PerfilCliente360")
    c1, c2 = st.columns([1, 2])
    with c1:
        solo_alertas = st.toggle("Solo clientes con alertas antifraude", value=True)
        texto = st.text_input("Buscar por nombre o código", placeholder="Ej.: Linda o 105")
    base = perfil[perfil["NroAnomalas"] > 0] if solo_alertas else perfil
    if texto:
        t = texto.strip().lower()
        base = base[base["Cliente"].str.lower().str.contains(t, regex=False)
                    | base["CustomerID"].astype(str).eq(t)]
    base = base.sort_values("MontoTransaccionado", ascending=False).head(300)
    if base.empty:
        st.warning("No se encontraron clientes con ese criterio.")
        return
    with c2:
        cid = st.selectbox("Cliente", base["CustomerID"].tolist(),
                           format_func=lambda c: f"{c} · {base.loc[base.CustomerID == c, 'Cliente'].iloc[0]}")

    resumen, trans, prest, tarj, feed = db.sp_perfil_cliente(int(cid))
    r = resumen.iloc[0]

    st.subheader(f"{r['Cliente']}  ·  {r['City']}")
    st.markdown(f'<span class="chip">Edad: {int(r["Age"])}</span><span class="chip">Género: {r["Gender"]}</span>'
                f'<span class="chip">{r["Email"]}</span>'
                f'<span class="chip">Cuartil de actividad: {int(r["CuartilActividad"])} de 4</span>'
                f'<span class="chip">Supera al {r["PctRankActividad"]:.0%} de los clientes</span>',
                unsafe_allow_html=True)

    k = st.columns(5)
    k[0].metric("Saldo en cuentas", soles(r["SaldoCuentas"]))
    k[1].metric("Monto transaccionado", soles(r["MontoTransaccionado"]))
    k[2].metric("Préstamos aprobados", soles(r["MontoPrestamosAprobados"]))
    k[3].metric("Deuda en tarjetas", soles(r["DeudaTarjetas"]))
    k[4].metric("Crédito disponible", soles(r["CreditoDisponible"]))

    if r["NroAnomalas"] > 0:
        st.error(f"⚠️ El cliente tiene {int(r['NroAnomalas'])} transacción(es) marcada(s) como anómala(s).")
    if r["CreditoDisponible"] < 0:
        st.warning("💳 La deuda de sus tarjetas supera el límite de crédito asignado.")
    if r["FeedbackPendiente"] > 0:
        st.info(f"📨 Tiene {int(r['FeedbackPendiente'])} caso(s) de atención pendiente(s).")

    t1, t2, t3, t4 = st.tabs(["Transacciones", "Préstamos", "Tarjetas de crédito", "Atención al cliente"])
    with t1:
        st.dataframe(trans, hide_index=True)
    with t2:
        st.dataframe(prest, hide_index=True)
    with t3:
        st.dataframe(tarj, hide_index=True)
    with t4:
        st.dataframe(feed, hide_index=True)
    mostrar(rp.fig_posicion_cliente(perfil, int(cid)))


# ---------------------------------------------------------------------------
# Página 5: Cartera y atención
# ---------------------------------------------------------------------------
def pagina_cartera():
    st.title("Cartera de préstamos, tarjetas y atención al cliente")
    t1, t2, t3 = st.tabs(["Préstamos", "Tarjetas de crédito", "Atención al cliente"])

    with t1:
        loans = leer(db, CLAVE, "SELECT * FROM dbo.Loan")
        tipos = st.multiselect("Tipo de préstamo", sorted(loans["LoanType"].unique()),
                               default=sorted(loans["LoanType"].unique()))
        lf = loans[loans["LoanType"].isin(tipos)]
        ap = lf[lf["LoanStatus"].isin(["Approved", "Closed"])]
        k = st.columns(4)
        k[0].metric("Solicitudes", f"{len(lf):,}")
        k[1].metric("Monto aprobado", soles(ap["LoanAmount"].sum()))
        k[2].metric("Tasa de aprobación", f"{len(ap) / len(lf):.1%}" if len(lf) else "-")
        k[3].metric("Tasa de interés promedio", f"{ap['InterestRate'].mean():.2f}%" if len(ap) else "-")
        mostrar(rp.fig_prestamos_mensual(lf))
        mostrar(rp.fig_prestamos_tipo(lf))

    with t2:
        cards = leer(db, CLAVE, "SELECT * FROM dbo.CreditCard")
        clientes = leer(db, CLAVE, "SELECT CustomerID, FirstName, LastName, Email FROM dbo.Customer")
        c1, c2 = st.columns([1, 1.3])
        with c1:
            mostrar(rp.fig_deuda_marca(cards))
        with c2:
            st.markdown("#### Vencimientos próximos")
            corte = st.date_input("Fecha de corte", dt.date(2023, 12, 20))
            dias = st.slider("Días hacia adelante", 1, 30, 7)
            lim = pd.Timestamp(corte) + pd.Timedelta(days=dias)
            ven = (cards[cards["PaymentDueDate"].between(pd.Timestamp(corte), lim)
                         & (cards["CreditCardBalance"] > 0)]
                   .merge(clientes, on="CustomerID")
                   .sort_values(["PaymentDueDate", "CreditCardBalance"], ascending=[True, False]))
            st.metric("Tarjetas por vencer con deuda", f"{len(ven):,}",
                      soles(ven["MinimumPaymentDue"].sum()) + " en pagos mínimos", delta_color="off")
            st.dataframe(ven[["CardID", "FirstName", "LastName", "Email", "CardType", "CreditCardBalance",
                              "MinimumPaymentDue", "PaymentDueDate"]], hide_index=True, height=260)
            descargar(ven, "recordatorios_pago.csv", "⬇️ Descargar lista de recordatorios")

    with t3:
        fb = leer(db, CLAVE, "SELECT * FROM dbo.Feedback")
        k = st.columns(3)
        k[0].metric("Registros de atención", f"{len(fb):,}")
        k[1].metric("Resueltos", f"{(fb['ResolutionStatus'] == 'Resolved').mean():.1%}")
        k[2].metric("Quejas", f"{(fb['FeedbackType'] == 'Complaint').sum():,}")
        mostrar(rp.fig_feedback_trimestre(fb))


# ---------------------------------------------------------------------------
# Página 6: Consultas SQL de las misiones
# ---------------------------------------------------------------------------
def pagina_consultas():
    st.title("Consultas SQL de las misiones")
    st.caption("25 consultas: 5 por misión, según los temas de las semanas 6-7, 9, 10, 11 y 13")

    c1, c2 = st.columns([1, 2.2])
    with c1:
        mision = st.selectbox("Misión", list(MISIONES),
                              format_func=lambda m: f"{m} · {MISIONES[m][0]} ({MISIONES[m][1]})")
        numeros = [c["n"] for c in CONSULTAS if c["mision"] == mision]
        n = st.radio("Consulta", numeros, format_func=lambda x: f"Q{x}", horizontal=True)
        q = next(c for c in CONSULTAS if c["n"] == n)
    with c2:
        st.markdown(f"**Q{q['n']}.** {q['pregunta']}")
        st.markdown(f"**Técnica:** {q['tecnica']}")
        st.markdown("".join(f'<span class="chip">{t}</span>' for t in q["tablas"]), unsafe_allow_html=True)
        st.code(q["tsql"], language="sql")
        st.markdown(f'<span class="nota">{q["explicacion"]}</span>', unsafe_allow_html=True)

    if st.button(f"▶️ Ejecutar Q{q['n']}", type="primary"):
        try:
            res = db.ejecutar_mision(q)
            st.success(f"{len(res):,} fila(s) devuelta(s)")
            st.dataframe(res, hide_index=True)
            descargar(res, f"Q{q['n']}.csv")
        except Exception as e:
            st.error(f"Error al ejecutar la consulta: {e}")
        if db.modo == "demo":
            st.caption("Modo demo: se ejecuta una versión equivalente en SQLite. "
                       "Con SQL Server se ejecuta el T-SQL mostrado.")

    with st.expander("Matriz de uso de tablas por consulta"):
        tablas = ["Customer", "Account", "Transaction", "Branch", "Loan", "CreditCard", "Feedback",
                  "Analyst", "Investigation"]
        m = pd.DataFrame([{**{"Q": f"Q{c['n']}"}, **{t: "✓" if t in c["tablas"] else "" for t in tablas}}
                          for c in CONSULTAS])
        st.dataframe(m, hide_index=True)


# ---------------------------------------------------------------------------
# Página 7: Modelo de datos
# ---------------------------------------------------------------------------
def pagina_modelo():
    st.title("Modelo de datos en 3FN")
    img = os.path.join(BASE, "assets", "modelo_relacional.png")
    if os.path.exists(img):
        st.image(img, caption="Modelo relacional implementado en SQL Server")
    conteo = leer(db, CLAVE, """
        SELECT 'Customer' AS Tabla, COUNT(*) AS Filas FROM dbo.Customer UNION ALL
        SELECT 'Account', COUNT(*) FROM dbo.Account UNION ALL
        SELECT 'Transaction', COUNT(*) FROM dbo.[Transaction] UNION ALL
        SELECT 'Branch', COUNT(*) FROM dbo.Branch UNION ALL
        SELECT 'Loan', COUNT(*) FROM dbo.Loan UNION ALL
        SELECT 'CreditCard', COUNT(*) FROM dbo.CreditCard UNION ALL
        SELECT 'Feedback', COUNT(*) FROM dbo.Feedback UNION ALL
        SELECT 'Analyst', COUNT(*) FROM dbo.Analyst UNION ALL
        SELECT 'Investigation', COUNT(*) FROM dbo.Investigation""")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(conteo, hide_index=True)
    with c2:
        st.markdown("""
**Objetos de base de datos que usa el aplicativo**

- `vw_TransaccionDetalle`: transacciones con cuenta, cliente y sucursal.
- `vw_InvestigacionDetalle`: asignaciones con analista, supervisor y dictamen vigente.
- `vw_PerfilCliente360`: un registro por cliente con todos sus productos, cuartil (NTILE) y percentil (PERCENT_RANK).
- `fn_SeveridadFraude`: función escalar que clasifica cada caso en Crítico, Alto, Medio o Bajo.
- `sp_DesempenoAnalistas`: procedimiento con parámetros y validación IF para el reporte del equipo de riesgo.
- `sp_PerfilCliente360`: procedimiento que devuelve el perfil completo de un cliente.
""")


PAGINAS = {
    "Resumen ejecutivo": pagina_resumen,
    "Monitoreo de fraude": pagina_fraude,
    "Equipo de riesgo": pagina_equipo,
    "Perfil 360° del cliente": pagina_perfil,
    "Cartera y atención": pagina_cartera,
    "Consultas SQL (misiones)": pagina_consultas,
    "Modelo de datos": pagina_modelo,
}
PAGINAS[pagina]()
st.markdown('<br><span class="nota">BancoVigía · Grupo 8 · Ingeniería de Datos · Universidad del Pacífico</span>',
            unsafe_allow_html=True)
