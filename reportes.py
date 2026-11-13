"""
reportes.py - Gráficos del aplicativo BancoVigía (matplotlib + seaborn).
Cada función recibe DataFrames ya filtrados y devuelve una figura de matplotlib.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

AZUL = "#1F3864"      # azul institucional
CELESTE = "#2E86AB"
ROJO = "#C0392B"
AMBAR = "#E67E22"
VERDE = "#27AE60"
GRIS = "#8C8C8C"
FONDO = "#FFFFFF"

COLOR_DICTAMEN = {"Fraud Confirmed": ROJO, "False Positive": VERDE, "Under Review": AMBAR}
ETIQUETA_DICTAMEN = {"Fraud Confirmed": "Fraude confirmado", "False Positive": "Falso positivo",
                     "Under Review": "En revisión"}
COLOR_SEVERIDAD = {"Crítico": "#7B1E1E", "Alto": ROJO, "Medio": AMBAR, "Bajo": VERDE}
ETIQUETA_TIPO = {"Deposit": "Depósito", "Withdrawal": "Retiro", "Transfer": "Transferencia"}
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlecolor": AZUL,
    "axes.labelcolor": "#333333",
    "axes.edgecolor": "#CCCCCC",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "figure.facecolor": FONDO,
    "axes.facecolor": FONDO,
    "axes.grid": True,
    "grid.color": "#EEEEEE",
    "grid.linewidth": 0.8,
})


def soles(x, _pos=None):
    if abs(x) >= 1_000_000:
        return f"S/ {x / 1_000_000:.1f} M"
    if abs(x) >= 1_000:
        return f"S/ {x / 1_000:.0f} mil"
    return f"S/ {x:,.0f}"


def _vacio(titulo):
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    ax.text(0.5, 0.5, "No hay datos para los filtros seleccionados", ha="center", va="center",
            color=GRIS, fontsize=11)
    ax.set_title(titulo)
    return fig


# ---------------------------------------------------------------------------
# Reporte 1: Resumen de operaciones
# ---------------------------------------------------------------------------
def fig_tendencia_mensual(td):
    titulo = "Monto transaccionado y alertas antifraude por mes"
    if td.empty:
        return _vacio(titulo)
    d = td.assign(Periodo=td["TransactionDate"].dt.to_period("M"))
    g = d.groupby("Periodo").agg(Monto=("TransactionAmount", "sum"),
                                 Anomalas=("Anomaly", lambda s: (s == -1).sum())).sort_index()
    etiquetas = [f"{MESES[p.month - 1]}\n{p.year}" if p.month == 1 or i == 0 else MESES[p.month - 1]
                 for i, p in enumerate(g.index)]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = np.arange(len(g))
    ax.bar(x, g["Monto"], color=CELESTE, width=0.65, label="Monto transaccionado")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(soles))
    ax.set_xticks(x, etiquetas)
    ax.set_ylabel("Monto")
    ax2 = ax.twinx()
    ax2.plot(x, g["Anomalas"], color=ROJO, marker="o", linewidth=2.2, label="Transacciones anómalas")
    ax2.set_ylabel("N.º de anómalas", color=ROJO)
    ax2.tick_params(axis="y", colors=ROJO)
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax2.set_ylim(0, max(g["Anomalas"].max() * 1.35, 1))
    for xi, v in zip(x, g["Anomalas"]):
        ax2.annotate(f"{v}", (xi, v), textcoords="offset points", xytext=(0, 7), ha="center",
                     color=ROJO, fontsize=8.5, fontweight="bold")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False, ncol=2)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_tipo_transaccion(td):
    titulo = "Monto por tipo de operación y estado antifraude"
    if td.empty:
        return _vacio(titulo)
    g = (td.assign(Tipo=td["TransactionType"].map(ETIQUETA_TIPO))
           .pivot_table(index="Tipo", columns="EstadoAntifraude", values="TransactionAmount",
                        aggfunc="sum", fill_value=0))
    for c in ["Normal", "Anómala"]:
        if c not in g:
            g[c] = 0
    g = g.loc[g.sum(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.barh(g.index, g["Normal"], color=CELESTE, label="Normal")
    ax.barh(g.index, g["Anómala"], left=g["Normal"], color=ROJO, label="Anómala")
    for i, (n, a) in enumerate(zip(g["Normal"], g["Anómala"])):
        tot = n + a
        ax.text(tot, i, f"  {soles(tot)}  ({a / tot:.1%} anómalo)" if tot else "", va="center", fontsize=9)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(soles))
    ax.set_xlim(0, g.sum(axis=1).max() * 1.6)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.grid(axis="y", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_cuentas(td):
    titulo = "Transacciones por tipo de cuenta"
    if td.empty:
        return _vacio(titulo)
    g = td["AccountType"].map({"Current": "Corriente", "Savings": "Ahorros"}).value_counts()
    fig, ax = plt.subplots(figsize=(4.2, 3.6))
    _c, _t, pcts = ax.pie(g.values, labels=g.index, colors=[AZUL, CELESTE], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.38, edgecolor="white"), autopct="%1.0f%%", pctdistance=0.8,
           textprops=dict(color="#333333"))
    for p in pcts:
        p.set_color("white"); p.set_fontweight("bold"); p.set_fontsize(9)
    ax.text(0, 0, f"{g.sum():,}\ntransacciones", ha="center", va="center", fontsize=10, color=AZUL,
            fontweight="bold")
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Reporte 2: Monitoreo de fraude
# ---------------------------------------------------------------------------
def fig_anomalias_ciudad(td, top=12):
    titulo = f"Ciudades con más transacciones anómalas (top {top})"
    an = td[td["Anomaly"] == -1]
    if an.empty:
        return _vacio(titulo)
    g = (td.groupby("BranchCity")
           .agg(Anomalas=("Anomaly", lambda s: (s == -1).sum()), Total=("Anomaly", "size")))
    g["Tasa"] = g["Anomalas"] / g["Total"]
    g = g.sort_values(["Anomalas", "Tasa"]).tail(top)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    colores = [ROJO if t >= g["Tasa"].quantile(0.75) else "#E8A49C" for t in g["Tasa"]]
    ax.barh(g.index, g["Anomalas"], color=colores)
    for i, (a, t) in enumerate(zip(g["Anomalas"], g["Tasa"])):
        ax.text(a + 0.2, i, f"{a}  ({t:.1%} del total)", va="center", fontsize=8.5)
    ax.set_xlim(0, g["Anomalas"].max() * 1.45)
    ax.set_xlabel("N.º de transacciones anómalas")
    ax.grid(axis="y", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_heatmap_ciudad_trimestre(td, top=12):
    titulo = "Monto anómalo por ciudad y trimestre (PIVOT)"
    an = td[td["Anomaly"] == -1]
    if an.empty:
        return _vacio(titulo)
    pv = an.pivot_table(index="BranchCity", columns="Trimestre", values="TransactionAmount",
                        aggfunc="sum", fill_value=0)
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        if q not in pv:
            pv[q] = 0
    pv = pv[["Q1", "Q2", "Q3", "Q4"]]
    pv = pv.loc[pv.sum(axis=1).sort_values(ascending=False).index[:top]]
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    sns.heatmap(pv / 1000, annot=True, fmt=".1f", cmap="Reds", linewidths=0.6, linecolor="white",
                cbar_kws={"label": "Miles de soles"}, ax=ax)
    ax.set_xlabel("Trimestre 2023")
    ax.set_ylabel("")
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_dictamenes(inv):
    titulo = "Dictamen vigente de los casos investigados"
    vig = inv[inv["EsDictamenVigente"] == 1]
    if vig.empty:
        return _vacio(titulo)
    g = vig["Verdict"].value_counts()
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    cunas, _t, pcts = ax.pie(g.values, colors=[COLOR_DICTAMEN.get(i, GRIS) for i in g.index], startangle=90,
                             counterclock=False, wedgeprops=dict(width=0.38, edgecolor="white"),
                             autopct="%1.0f%%", pctdistance=0.81)
    for p in pcts:
        p.set_color("white"); p.set_fontweight("bold")
    ax.text(0, 0, f"{g.sum()}\ncasos", ha="center", va="center", fontsize=11, color=AZUL, fontweight="bold")
    ax.legend(cunas, [f"{ETIQUETA_DICTAMEN.get(i, i)} ({v})" for i, v in zip(g.index, g.values)],
              loc="upper center", bbox_to_anchor=(0.5, 0.0), frameon=False, ncol=3, fontsize=8.5)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_severidad(sev):
    titulo = "Casos por nivel de severidad"
    if sev.empty:
        return _vacio(titulo)
    orden = ["Crítico", "Alto", "Medio", "Bajo"]
    g = sev.groupby("Severidad").agg(Casos=("TransactionID", "count"),
                                     Monto=("TransactionAmount", "sum")).reindex(orden).fillna(0)
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    barras = ax.bar(g.index, g["Casos"], color=[COLOR_SEVERIDAD[o] for o in orden])
    for b, m in zip(barras, g["Monto"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(b.get_height())}\n{soles(m)}",
                ha="center", va="bottom", fontsize=8.5)
    ax.set_ylim(0, g["Casos"].max() * 1.3)
    ax.set_ylabel("N.º de casos")
    ax.grid(axis="x", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Reporte 3: Equipo de riesgo
# ---------------------------------------------------------------------------
def fig_desempeno(df):
    titulo = "Casos por analista según dictamen"
    if df is None or df.empty:
        return _vacio(titulo)
    d = df.sort_values("CasosAsignados")
    fig, ax = plt.subplots(figsize=(7.5, max(3.2, 0.32 * len(d) + 1)))
    izq = np.zeros(len(d))
    for col, ver in [("FraudesConfirmados", "Fraud Confirmed"), ("FalsosPositivos", "False Positive"),
                     ("EnRevision", "Under Review")]:
        ax.barh(d["Analista"], d[col], left=izq, color=COLOR_DICTAMEN[ver], label=ETIQUETA_DICTAMEN[ver])
        izq += d[col].values
    for i, (tot, pct) in enumerate(zip(d["CasosAsignados"], d["PctCasosCerrados"])):
        ax.text(tot + 0.2, i, f"{tot}  ({pct:.0f}% cerrados)", va="center", fontsize=8.5)
    ax.set_xlim(0, d["CasosAsignados"].max() * 1.4)
    ax.set_xlabel("N.º de casos")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="y", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_tiempo_respuesta(df):
    titulo = "Promedio de días hasta tomar el caso"
    if df is None or df.empty:
        return _vacio(titulo)
    d = df.sort_values("PromDiasAsignacion")
    prom = (d["PromDiasAsignacion"] * d["CasosAsignados"]).sum() / d["CasosAsignados"].sum()
    fig, ax = plt.subplots(figsize=(5.6, max(3.2, 0.32 * len(d) + 1)))
    colores = [ROJO if v > prom else CELESTE for v in d["PromDiasAsignacion"]]
    ax.barh(d["Analista"], d["PromDiasAsignacion"], color=colores)
    ax.axvline(prom, color=AZUL, linestyle="--", linewidth=1.4)
    ax.text(prom, len(d) - 0.4, f" promedio {prom:.1f} días", color=AZUL, fontsize=8.5, va="bottom")
    ax.set_xlabel("Días")
    ax.grid(axis="y", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Reporte 4: Cartera de préstamos, tarjetas y atención
# ---------------------------------------------------------------------------
def fig_prestamos_mensual(loans):
    titulo = "Préstamos aprobados por mes y variación frente al mes anterior (LAG)"
    ap = loans[loans["LoanStatus"].isin(["Approved", "Closed"])]
    if ap.empty:
        return _vacio(titulo)
    g = (ap.assign(Periodo=ap["ApprovalRejectionDate"].dt.to_period("M"))
           .groupby("Periodo")["LoanAmount"].sum().sort_index())
    var = g.pct_change() * 100
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True,
                                   gridspec_kw=dict(height_ratios=[2.2, 1]))
    x = np.arange(len(g))
    ax1.plot(x, g.values, color=AZUL, linewidth=2.2, marker="o", markersize=3.5)
    ax1.fill_between(x, g.values, color=AZUL, alpha=0.08)
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(soles))
    ax1.set_title(titulo, loc="left")
    ax2.bar(x, var.fillna(0).values, color=[VERDE if v >= 0 else ROJO for v in var.fillna(0)])
    ax2.axhline(0, color="#999999", linewidth=0.8)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax2.set_ylabel("Var. %")
    paso = max(1, len(g) // 12)
    ax2.set_xticks(x[::paso], [f"{MESES[p.month - 1]} {str(p.year)[2:]}" for p in g.index[::paso]],
                   rotation=0, fontsize=8.5)
    fig.tight_layout()
    return fig


def fig_prestamos_tipo(loans):
    titulo = "Préstamos por tipo y estado"
    if loans.empty:
        return _vacio(titulo)
    tipos = {"Mortgage": "Hipotecario", "Auto": "Vehicular", "Personal": "Personal"}
    estados = {"Approved": "Aprobado", "Closed": "Cerrado", "Rejected": "Rechazado"}
    pv = (loans.assign(Tipo=loans["LoanType"].map(tipos).fillna(loans["LoanType"]),
                       Estado=loans["LoanStatus"].map(estados).fillna(loans["LoanStatus"]))
               .pivot_table(index="Tipo", columns="Estado", values="LoanAmount", aggfunc="sum", fill_value=0))
    fig, ax = plt.subplots(figsize=(6, 3.8))
    colores = {"Aprobado": VERDE, "Cerrado": CELESTE, "Rechazado": ROJO}
    pv.plot(kind="bar", ax=ax, color=[colores.get(c, GRIS) for c in pv.columns], width=0.75, rot=0)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(soles))
    ax.set_ylim(0, pv.values.max() * 1.18)
    ax.set_xlabel("")
    ax.legend(frameon=False, title="", ncol=3, loc="upper center")
    ax.grid(axis="x", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_deuda_marca(cards):
    titulo = "Participación en la deuda de tarjetas por marca"
    if cards.empty:
        return _vacio(titulo)
    g = cards.groupby("CardType")["CreditCardBalance"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    _c, _t, pcts = ax.pie(g.values, labels=g.index, colors=[AZUL, CELESTE, "#9DC3E6"], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.38, edgecolor="white"), autopct="%1.1f%%", pctdistance=0.8,
           textprops=dict(color="#333333"))
    for p in pcts:
        p.set_color("white"); p.set_fontweight("bold"); p.set_fontsize(9)
    ax.text(0, 0, f"{soles(g.sum())}\nde deuda", ha="center", va="center", fontsize=10, color=AZUL,
            fontweight="bold")
    ax.set_title(titulo)
    fig.tight_layout()
    return fig


def fig_feedback_trimestre(fb):
    titulo = "% de casos de atención resueltos por trimestre"
    if fb.empty:
        return _vacio(titulo)
    tipos = {"Complaint": "Queja", "Suggestion": "Sugerencia", "Praise": "Felicitación"}
    d = fb.assign(Trimestre="Q" + fb["FeedbackDate"].dt.quarter.astype(str),
                  Tipo=fb["FeedbackType"].map(tipos).fillna(fb["FeedbackType"]),
                  Resuelto=(fb["ResolutionStatus"] == "Resolved").astype(int))
    pv = d.pivot_table(index="Trimestre", columns="Tipo", values="Resuelto", aggfunc="mean") * 100
    fig, ax = plt.subplots(figsize=(6, 3.8))
    colores = {"Queja": ROJO, "Sugerencia": AMBAR, "Felicitación": VERDE}
    pv.plot(kind="bar", ax=ax, color=[colores.get(c, GRIS) for c in pv.columns], width=0.75, rot=0)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 100)
    ax.axhline(50, color="#999999", linestyle=":", linewidth=1)
    ax.set_xlabel("")
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    ax.grid(axis="x", visible=False)
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Perfil 360°
# ---------------------------------------------------------------------------
def fig_posicion_cliente(perfil, customer_id):
    titulo = "Posición del cliente frente a la cartera (monto transaccionado)"
    if perfil.empty:
        return _vacio(titulo)
    fig, ax = plt.subplots(figsize=(8, 2.6))
    sns.histplot(perfil["MontoTransaccionado"], bins=40, color="#BFD7EA", edgecolor="white", ax=ax)
    fila = perfil[perfil["CustomerID"] == customer_id]
    if not fila.empty:
        v = float(fila["MontoTransaccionado"].iloc[0])
        ax.axvline(v, color=ROJO, linewidth=2.2)
        derecha = v > perfil["MontoTransaccionado"].max() * 0.6
        ax.text(v, ax.get_ylim()[1] * 0.92, f"este cliente: {soles(v)}  " if derecha else f"  este cliente: {soles(v)}",
                color=ROJO, fontsize=9, fontweight="bold", va="top", ha="right" if derecha else "left",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(soles))
    ax.set_xlabel("")
    ax.set_ylabel("Clientes")
    ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig
