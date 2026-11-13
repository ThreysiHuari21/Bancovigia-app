"""
db.py - Capa de acceso a datos del aplicativo BancoVigía.

Modo 1 (principal): SQL Server mediante pyodbc, sobre la base BancoVigia
                    creada con 01_BancoVigia_3FN.sql y 03_Vistas_Funcion_Procedimientos.sql.
Modo 2 (respaldo):  base demo en SQLite (data/BancoVigia_demo.db) con las mismas
                    tablas y vistas, para presentar el aplicativo sin SQL Server.
"""
import decimal
import os
import sqlite3

import pandas as pd

try:
    import pyodbc
except ImportError:          # el modo demo funciona aunque pyodbc no esté instalado
    pyodbc = None

RUTA_DEMO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "BancoVigia_demo.db")

COLUMNAS_FECHA = {
    "TransactionDate", "AssignmentDate", "ApprovalRejectionDate", "PaymentDueDate",
    "LastCreditCardPaymentDate", "FeedbackDate", "ResolutionDate", "DateOfAccountOpening",
    "UltimaTransaccion",
}


def severidad_fraude(verdict, amount):
    """Misma regla que dbo.fn_SeveridadFraude (se registra en SQLite para el modo demo)."""
    if verdict == "Fraud Confirmed" and amount >= 3000:
        return "Crítico"
    if verdict == "Fraud Confirmed" or (verdict == "Under Review" and amount >= 3000):
        return "Alto"
    if verdict == "Under Review":
        return "Medio"
    return "Bajo"


def drivers_disponibles():
    if pyodbc is None:
        return []
    return [d for d in pyodbc.drivers() if "SQL Server" in d]


def _normalizar(df):
    """pyodbc devuelve Decimal y date: se convierten a float y datetime para pandas."""
    for col in df.columns:
        if df[col].dtype == object and len(df[col].dropna()):
            muestra = df[col].dropna().iloc[0]
            if isinstance(muestra, decimal.Decimal):
                df[col] = df[col].astype(float)
        if col in COLUMNAS_FECHA:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


class BaseDatos:
    def __init__(self, modo="demo", servidor="localhost", driver=None,
                 base="BancoVigia", usuario=None, clave=None):
        self.modo = modo
        self.descripcion = ""
        if modo == "sqlserver":
            if pyodbc is None:
                raise RuntimeError("pyodbc no está instalado (pip install pyodbc).")
            driver = driver or (drivers_disponibles() or ["ODBC Driver 17 for SQL Server"])[-1]
            cadena = (f"DRIVER={{{driver}}};SERVER={servidor};DATABASE={base};"
                      "Encrypt=no;TrustServerCertificate=yes;")
            if usuario:
                cadena += f"UID={usuario};PWD={clave};"
            else:
                cadena += "Trusted_Connection=yes;"
            self.cn = pyodbc.connect(cadena, timeout=5)
            self.descripcion = f"SQL Server · {servidor} · {base}"
        else:
            if not os.path.exists(RUTA_DEMO):
                raise RuntimeError("No se encontró data/BancoVigia_demo.db (ejecuta crear_demo_db.py).")
            self.cn = sqlite3.connect(RUTA_DEMO, check_same_thread=False)
            self.cn.create_function("fn_SeveridadFraude", 2, severidad_fraude)
            self.descripcion = "Modo demo · SQLite local"

    # ------------------------------------------------------------------
    def _sql(self, sql):
        return sql.replace("dbo.", "") if self.modo == "demo" else sql

    @staticmethod
    def _leer_cursor(cur):
        """Devuelve todos los conjuntos de resultados de un lote (SP, SQL dinámico)."""
        tablas = []
        while True:
            if cur.description is not None:
                cols = [c[0] for c in cur.description]
                filas = [tuple(f) for f in cur.fetchall()]
                tablas.append(_normalizar(pd.DataFrame(filas, columns=cols)))
            if not hasattr(cur, "nextset"):
                break
            try:
                if not cur.nextset():
                    break
            except Exception:
                break
        return tablas

    def consultar(self, sql, params=None):
        tablas = self.consultar_varias(sql, params)
        return tablas[0] if tablas else pd.DataFrame()

    def consultar_varias(self, sql, params=None):
        cur = self.cn.cursor()
        cur.execute(self._sql(sql), params or [])
        tablas = self._leer_cursor(cur)
        cur.close()
        return tablas

    # ------------------------------------------------------------------
    # Procedimientos almacenados
    # ------------------------------------------------------------------
    def sp_desempeno_analistas(self, fecha_ini, fecha_fin, branch_id=None, verdict=None):
        if self.modo == "sqlserver":
            sql = ("SET NOCOUNT ON; EXEC dbo.sp_DesempenoAnalistas "
                   "@FechaInicio = ?, @FechaFin = ?, @BranchID = ?, @Verdict = ?;")
            return self.consultar(sql, [fecha_ini, fecha_fin, branch_id, verdict])
        # Modo demo: misma lógica que el procedimiento
        inv = self.consultar("SELECT * FROM vw_InvestigacionDetalle")
        m = inv["AssignmentDate"].between(pd.Timestamp(fecha_ini), pd.Timestamp(fecha_fin))
        if branch_id is not None:
            m &= inv["BranchID"] == branch_id
        if verdict is not None:
            m &= inv["Verdict"] == verdict
        d = inv[m]
        if d.empty:
            return pd.DataFrame()
        g = (d.groupby(["AnalystID", "Analista", "Supervisor", "BranchName"])
               .agg(CasosAsignados=("TransactionID", "count"),
                    FraudesConfirmados=("Verdict", lambda s: (s == "Fraud Confirmed").sum()),
                    FalsosPositivos=("Verdict", lambda s: (s == "False Positive").sum()),
                    EnRevision=("Verdict", lambda s: (s == "Under Review").sum()),
                    MontoInvestigado=("TransactionAmount", "sum"),
                    PromDiasAsignacion=("DiasHastaAsignacion", "mean"))
               .reset_index())
        g["PctCasosCerrados"] = (100 * (g.CasosAsignados - g.EnRevision) / g.CasosAsignados).round(2)
        g["PromDiasAsignacion"] = g["PromDiasAsignacion"].round(2)
        g["Ranking"] = g["CasosAsignados"].rank(method="min", ascending=False).astype(int)
        g = g.sort_values(["Ranking", "AnalystID"]).reset_index(drop=True)
        n = len(g)
        g["Segmento"] = [1 + (i * 3) // n for i in range(n)]   # NTILE(3)
        return g

    def sp_perfil_cliente(self, customer_id):
        """Devuelve [resumen, transacciones, préstamos, tarjetas, feedback]."""
        if self.modo == "sqlserver":
            return self.consultar_varias(
                "SET NOCOUNT ON; EXEC dbo.sp_PerfilCliente360 @CustomerID = ?;", [customer_id])
        p = [customer_id]
        return [
            self.consultar("SELECT * FROM vw_PerfilCliente360 WHERE CustomerID = ?", p),
            self.consultar("""
                SELECT TD.TransactionID, TD.TransactionDate, TD.TransactionType,
                       TD.TransactionAmount, TD.EstadoAntifraude, TD.BranchName,
                       IFNULL(INV.Verdict, '-') AS DictamenVigente
                FROM vw_TransaccionDetalle TD
                LEFT JOIN vw_InvestigacionDetalle INV
                       ON INV.TransactionID = TD.TransactionID AND INV.EsDictamenVigente = 1
                WHERE TD.CustomerID = ? ORDER BY TD.TransactionDate DESC""", p),
            self.consultar("""SELECT LoanID, LoanType, LoanAmount, InterestRate, LoanTerm,
                                     ApprovalRejectionDate, LoanStatus
                              FROM Loan WHERE CustomerID = ?""", p),
            self.consultar("""SELECT CardID, CardType, CreditLimit, CreditCardBalance, AvailableCredit,
                                     MinimumPaymentDue, PaymentDueDate, LastCreditCardPaymentDate, RewardsPoints
                              FROM CreditCard WHERE CustomerID = ?""", p),
            self.consultar("""SELECT FeedbackID, FeedbackDate, FeedbackType, ResolutionStatus, ResolutionDate
                              FROM Feedback WHERE CustomerID = ?""", p),
        ]

    # ------------------------------------------------------------------
    def ejecutar_mision(self, consulta):
        """Ejecuta una consulta de las misiones: T-SQL en SQL Server, versión equivalente en demo."""
        if self.modo == "sqlserver":
            return self.consultar("SET NOCOUNT ON;\n" + consulta["tsql"])
        return self.consultar(consulta["lite"])
