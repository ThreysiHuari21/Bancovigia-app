"""
crear_demo_db.py - Construye data/BancoVigia_demo.db (SQLite) a partir de los CSV
normalizados en data/csv. Replica las tablas en 3FN y las vistas del script
03_Vistas_Funcion_Procedimientos.sql para usar el aplicativo sin SQL Server.

Uso:  python crear_demo_db.py
"""
import os
import sqlite3

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(BASE, "data", "csv")
DB = os.path.join(BASE, "data", "BancoVigia_demo.db")

DDL = """
CREATE TABLE Branch (BranchID INTEGER PRIMARY KEY, BranchName TEXT NOT NULL, BranchCity TEXT NOT NULL);
CREATE TABLE Customer (CustomerID INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, Age INTEGER, Gender TEXT,
    Address TEXT, City TEXT, ContactNumber INTEGER, Email TEXT);
CREATE TABLE Account (AccountID INTEGER PRIMARY KEY, CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
    AccountType TEXT NOT NULL CHECK (AccountType IN ('Current','Savings')), AccountBalance REAL,
    DateOfAccountOpening TEXT, OverdraftLine REAL, AccountInterestRate REAL);
CREATE TABLE "Transaction" (TransactionID INTEGER PRIMARY KEY, AccountID INTEGER NOT NULL REFERENCES Account(AccountID),
    BranchID INTEGER NOT NULL REFERENCES Branch(BranchID), TransactionDate TEXT NOT NULL, TransactionType TEXT NOT NULL,
    TransactionAmount REAL NOT NULL, AccountBalanceAfterTransaction REAL, Anomaly INTEGER NOT NULL CHECK (Anomaly IN (-1, 1)));
CREATE TABLE Loan (LoanID INTEGER PRIMARY KEY, CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID), LoanAmount REAL,
    LoanType TEXT, InterestRate REAL, LoanTerm INTEGER, ApprovalRejectionDate TEXT, LoanStatus TEXT);
CREATE TABLE CreditCard (CardID INTEGER PRIMARY KEY, CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID), CardType TEXT,
    CreditLimit REAL, CreditCardBalance REAL, MinimumPaymentDue REAL, PaymentDueDate TEXT, LastCreditCardPaymentDate TEXT,
    RewardsPoints INTEGER, AvailableCredit REAL GENERATED ALWAYS AS (CreditLimit - CreditCardBalance) VIRTUAL);
CREATE TABLE Feedback (FeedbackID INTEGER PRIMARY KEY, CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
    FeedbackDate TEXT, FeedbackType TEXT, ResolutionStatus TEXT, ResolutionDate TEXT);
CREATE TABLE Analyst (AnalystID INTEGER PRIMARY KEY, AnalystFirstName TEXT NOT NULL, AnalystLastName TEXT NOT NULL,
    BranchID INTEGER NOT NULL REFERENCES Branch(BranchID), SupervisorID INTEGER REFERENCES Analyst(AnalystID));
CREATE TABLE Investigation (TransactionID INTEGER NOT NULL REFERENCES "Transaction"(TransactionID),
    AnalystID INTEGER NOT NULL REFERENCES Analyst(AnalystID), AssignmentDate TEXT NOT NULL, Verdict TEXT NOT NULL,
    PRIMARY KEY (TransactionID, AnalystID));

CREATE VIEW vw_TransaccionDetalle AS
SELECT T.TransactionID, T.TransactionDate,
       CAST(strftime('%Y', T.TransactionDate) AS INTEGER) AS Anio,
       CAST(strftime('%m', T.TransactionDate) AS INTEGER) AS Mes,
       'Q' || ((CAST(strftime('%m', T.TransactionDate) AS INTEGER) + 2) / 3) AS Trimestre,
       T.TransactionType, T.TransactionAmount, T.AccountBalanceAfterTransaction, T.Anomaly,
       CASE WHEN T.Anomaly = -1 THEN 'Anómala' ELSE 'Normal' END AS EstadoAntifraude,
       A.AccountID, A.AccountType, C.CustomerID, C.FirstName || ' ' || C.LastName AS Cliente,
       C.City AS CiudadCliente, B.BranchID, B.BranchName, B.BranchCity
FROM "Transaction" T JOIN Account A ON A.AccountID = T.AccountID
JOIN Customer C ON C.CustomerID = A.CustomerID JOIN Branch B ON B.BranchID = T.BranchID;

CREATE VIEW vw_InvestigacionDetalle AS
SELECT I.TransactionID, I.AnalystID, AN.AnalystFirstName || ' ' || AN.AnalystLastName AS Analista,
       IFNULL(S.AnalystFirstName || ' ' || S.AnalystLastName, 'Sin supervisor') AS Supervisor,
       B.BranchID, B.BranchName, B.BranchCity, T.TransactionDate, T.TransactionType, T.TransactionAmount,
       I.AssignmentDate, CAST(julianday(I.AssignmentDate) - julianday(T.TransactionDate) AS INTEGER) AS DiasHastaAsignacion,
       I.Verdict,
       CASE WHEN ROW_NUMBER() OVER (PARTITION BY I.TransactionID ORDER BY I.AssignmentDate DESC) = 1 THEN 1 ELSE 0 END AS EsDictamenVigente
FROM Investigation I JOIN "Transaction" T ON T.TransactionID = I.TransactionID
JOIN Analyst AN ON AN.AnalystID = I.AnalystID JOIN Branch B ON B.BranchID = AN.BranchID
LEFT JOIN Analyst S ON S.AnalystID = AN.SupervisorID;

CREATE VIEW vw_PerfilCliente360 AS
WITH Cuentas AS (SELECT CustomerID, COUNT(*) NroCuentas, SUM(AccountBalance) SaldoCuentas FROM Account GROUP BY CustomerID),
Movimientos AS (SELECT A.CustomerID, COUNT(T.TransactionID) NroTransacciones, SUM(T.TransactionAmount) MontoTransaccionado,
    SUM(CASE WHEN T.Anomaly = -1 THEN 1 ELSE 0 END) NroAnomalas, MAX(T.TransactionDate) UltimaTransaccion
    FROM Account A JOIN "Transaction" T ON T.AccountID = A.AccountID GROUP BY A.CustomerID),
Prestamos AS (SELECT CustomerID, SUM(CASE WHEN LoanStatus IN ('Approved','Closed') THEN LoanAmount ELSE 0 END) MontoPrestamosAprobados,
    COUNT(*) NroPrestamos FROM Loan GROUP BY CustomerID),
Tarjetas AS (SELECT CustomerID, COUNT(*) NroTarjetas, SUM(CreditCardBalance) DeudaTarjetas, SUM(AvailableCredit) CreditoDisponible
    FROM CreditCard GROUP BY CustomerID),
Atencion AS (SELECT CustomerID, COUNT(*) NroFeedback, SUM(CASE WHEN ResolutionStatus = 'Pending' THEN 1 ELSE 0 END) FeedbackPendiente
    FROM Feedback GROUP BY CustomerID)
SELECT C.CustomerID, C.FirstName || ' ' || C.LastName AS Cliente, C.Age, C.Gender, C.City, C.Email,
    IFNULL(CU.NroCuentas,0) NroCuentas, IFNULL(CU.SaldoCuentas,0) SaldoCuentas,
    IFNULL(M.NroTransacciones,0) NroTransacciones, IFNULL(M.MontoTransaccionado,0) MontoTransaccionado,
    IFNULL(M.NroAnomalas,0) NroAnomalas, M.UltimaTransaccion,
    IFNULL(P.NroPrestamos,0) NroPrestamos, IFNULL(P.MontoPrestamosAprobados,0) MontoPrestamosAprobados,
    IFNULL(TJ.NroTarjetas,0) NroTarjetas, IFNULL(TJ.DeudaTarjetas,0) DeudaTarjetas, IFNULL(TJ.CreditoDisponible,0) CreditoDisponible,
    IFNULL(AT.NroFeedback,0) NroFeedback, IFNULL(AT.FeedbackPendiente,0) FeedbackPendiente,
    NTILE(4) OVER (ORDER BY IFNULL(M.MontoTransaccionado,0) DESC) AS CuartilActividad,
    ROUND(PERCENT_RANK() OVER (ORDER BY IFNULL(M.MontoTransaccionado,0)), 2) AS PctRankActividad
FROM Customer C LEFT JOIN Cuentas CU ON CU.CustomerID = C.CustomerID LEFT JOIN Movimientos M ON M.CustomerID = C.CustomerID
LEFT JOIN Prestamos P ON P.CustomerID = C.CustomerID LEFT JOIN Tarjetas TJ ON TJ.CustomerID = C.CustomerID
LEFT JOIN Atencion AT ON AT.CustomerID = C.CustomerID;
"""

ORDEN = ["Branch", "Customer", "Account", "Transaction", "Loan", "CreditCard", "Feedback", "Analyst", "Investigation"]


def main():
    if os.path.exists(DB):
        os.remove(DB)
    cn = sqlite3.connect(DB)
    cn.executescript(DDL)
    for t in ORDEN:
        df = pd.read_csv(os.path.join(CSV, f"{t}.csv"))
        cols = ", ".join(df.columns)
        marcas = ", ".join("?" * len(df.columns))
        filas = [tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in r)
                 for r in df.itertuples(index=False)]
        cn.executemany(f'INSERT INTO "{t}" ({cols}) VALUES ({marcas})', filas)
        print(f"{t:<14} {len(df):>5} filas")
    cn.commit()
    cn.close()
    print("Base demo creada en", DB)


if __name__ == "__main__":
    main()
