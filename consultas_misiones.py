"""Las 25 consultas de las misiones (T-SQL) y su versión equivalente para el modo demo (SQLite)."""

MISIONES = {
    "M1": ("Mapeando el negocio", "Semanas 6 y 7"),
    "M2": ("Trazando conexiones", "Semana 9"),
    "M3": ("Midiendo el tiempo", "Semana 10"),
    "M4": ("Descubriendo quién lidera", "Semana 11"),
    "M5": ("Construyendo el reporte", "Semana 13"),
}

CONSULTAS = [{'n': 1,
  'mision': 'M1',
  'nombre_mision': 'Mapeando el negocio',
  'semana': 'Semanas 6 y 7',
  'pregunta': '¿Qué transacciones superan S/ 4,000 de monto y además están marcadas como anómalas por el '
              'sistema antifraude (Anomaly = -1)?',
  'tecnica': 'WHERE con dos condiciones (AND), INNER JOIN',
  'tablas': ['Transaction', 'Account', 'Customer', 'Branch'],
  'tsql': 'SELECT T.TransactionID,\n'
          '       T.TransactionDate,\n'
          '       T.TransactionType,\n'
          '       T.TransactionAmount,\n'
          "       C.FirstName + ' ' + C.LastName AS Cliente,\n"
          '       A.AccountType,\n'
          '       B.BranchName,\n'
          '       B.BranchCity\n'
          'FROM dbo.[Transaction] AS T\n'
          'JOIN dbo.Account  AS A ON A.AccountID  = T.AccountID\n'
          'JOIN dbo.Customer AS C ON C.CustomerID = A.CustomerID\n'
          'JOIN dbo.Branch   AS B ON B.BranchID   = T.BranchID\n'
          'WHERE T.TransactionAmount > 4000      -- condición 1: umbral de monto\n'
          '  AND T.Anomaly = -1                  -- condición 2: marcada como anómala\n'
          'ORDER BY T.TransactionAmount DESC;',
  'lite': 'SELECT T.TransactionID, T.TransactionDate, T.TransactionType, T.TransactionAmount,\n'
          "       C.FirstName || ' ' || C.LastName AS Cliente, A.AccountType, B.BranchName, B.BranchCity\n"
          'FROM "Transaction" T JOIN Account A ON A.AccountID=T.AccountID\n'
          'JOIN Customer C ON C.CustomerID=A.CustomerID JOIN Branch B ON B.BranchID=T.BranchID\n'
          'WHERE T.TransactionAmount > 4000 AND T.Anomaly = -1\n'
          'ORDER BY T.TransactionAmount DESC;',
  'explicacion': 'Filtra las transacciones que cumplen las dos condiciones a la vez. Los JOIN agregan el '
                 'cliente, el tipo de cuenta y la sucursal para que el área de Riesgos sepa a quién y dónde '
                 'corresponde cada caso.'},
 {'n': 2,
  'mision': 'M1',
  'nombre_mision': 'Mapeando el negocio',
  'semana': 'Semanas 6 y 7',
  'pregunta': '¿Qué transacciones anómalas ya fueron asignadas a un analista de riesgo, pero todavía no '
              "tienen ningún dictamen final (todas sus revisiones siguen en 'Under Review')?",
  'tecnica': 'Operadores de conjuntos: EXCEPT (diferencia entre dos consultas)',
  'tablas': ['Investigation', 'Transaction', 'Branch'],
  'tsql': '-- Conjunto A: transacciones que tienen al menos una asignación\n'
          'SELECT T.TransactionID,\n'
          '       T.TransactionDate,\n'
          '       T.TransactionAmount,\n'
          '       B.BranchName\n'
          'FROM dbo.Investigation AS I\n'
          'JOIN dbo.[Transaction] AS T ON T.TransactionID = I.TransactionID\n'
          'JOIN dbo.Branch        AS B ON B.BranchID      = T.BranchID\n'
          '\n'
          'EXCEPT\n'
          '\n'
          '-- Conjunto B: transacciones que ya tienen un dictamen final\n'
          'SELECT T.TransactionID,\n'
          '       T.TransactionDate,\n'
          '       T.TransactionAmount,\n'
          '       B.BranchName\n'
          'FROM dbo.Investigation AS I\n'
          'JOIN dbo.[Transaction] AS T ON T.TransactionID = I.TransactionID\n'
          'JOIN dbo.Branch        AS B ON B.BranchID      = T.BranchID\n'
          "WHERE I.Verdict <> 'Under Review'\n"
          '\n'
          'ORDER BY TransactionDate;',
  'lite': 'SELECT T.TransactionID, T.TransactionDate, T.TransactionAmount, B.BranchName\n'
          'FROM Investigation I JOIN "Transaction" T ON T.TransactionID=I.TransactionID JOIN Branch B ON '
          'B.BranchID=T.BranchID\n'
          'EXCEPT\n'
          'SELECT T.TransactionID, T.TransactionDate, T.TransactionAmount, B.BranchName\n'
          'FROM Investigation I JOIN "Transaction" T ON T.TransactionID=I.TransactionID JOIN Branch B ON '
          'B.BranchID=T.BranchID\n'
          "WHERE I.Verdict <> 'Under Review' ORDER BY TransactionDate;",
  'explicacion': 'EXCEPT devuelve las filas del primer conjunto que no aparecen en el segundo. Al primer '
                 'grupo (casos asignados) se le restan los casos que ya tienen un dictamen final, así que '
                 'solo quedan los que siguen abiertos. Un caso escalado que el supervisor ya cerró no '
                 'aparece.'},
 {'n': 3,
  'mision': 'M1',
  'nombre_mision': 'Mapeando el negocio',
  'semana': 'Semanas 6 y 7',
  'pregunta': '¿Cuántas transacciones realizadas en cuentas de ahorros (Savings) tienen un monto en el rango '
              'intermedio de S/ 1,000 a S/ 3,000, y cuánto suman?',
  'tecnica': 'BETWEEN y funciones de agregación (COUNT, SUM, AVG)',
  'tablas': ['Transaction', 'Account'],
  'tsql': 'SELECT A.AccountType,\n'
          '       COUNT(*)                  AS CantidadTransacciones,\n'
          '       SUM(T.TransactionAmount)  AS MontoTotal,\n'
          '       AVG(T.TransactionAmount)  AS MontoPromedio\n'
          'FROM dbo.[Transaction] AS T\n'
          'JOIN dbo.Account       AS A ON A.AccountID = T.AccountID\n'
          "WHERE A.AccountType = 'Savings'\n"
          '  AND T.TransactionAmount BETWEEN 1000 AND 3000\n'
          'GROUP BY A.AccountType;',
  'lite': 'SELECT A.AccountType, COUNT(*), ROUND(SUM(T.TransactionAmount),2), '
          'ROUND(AVG(T.TransactionAmount),2)\n'
          'FROM "Transaction" T JOIN Account A ON A.AccountID=T.AccountID\n'
          "WHERE A.AccountType='Savings' AND T.TransactionAmount BETWEEN 1000 AND 3000\n"
          'GROUP BY A.AccountType;',
  'explicacion': 'BETWEEN incluye los dos extremos. Se usa el rango de S/ 1,000 a S/ 3,000 porque ninguna '
                 'transacción del dataset supera los S/ 5,000.'},
 {'n': 4,
  'mision': 'M1',
  'nombre_mision': 'Mapeando el negocio',
  'semana': 'Semanas 6 y 7',
  'pregunta': '¿Cuáles son los 3 clientes que acumulan el mayor saldo de deuda sumando todas sus tarjetas de '
              'crédito?',
  'tecnica': 'TOP con WITH TIES, GROUP BY y SUM',
  'tablas': ['Customer', 'CreditCard'],
  'tsql': 'SELECT TOP 3 WITH TIES\n'
          '       C.CustomerID,\n'
          "       C.FirstName + ' ' + C.LastName AS Cliente,\n"
          '       C.City,\n'
          '       COUNT(CC.CardID)          AS CantidadTarjetas,\n'
          '       SUM(CC.CreditCardBalance) AS DeudaTotal\n'
          'FROM dbo.Customer   AS C\n'
          'JOIN dbo.CreditCard AS CC ON CC.CustomerID = C.CustomerID\n'
          'GROUP BY C.CustomerID, C.FirstName, C.LastName, C.City\n'
          'ORDER BY DeudaTotal DESC;',
  'lite': "SELECT C.CustomerID, C.FirstName || ' ' || C.LastName, C.City, COUNT(CC.CardID), "
          'SUM(CC.CreditCardBalance) AS DeudaTotal\n'
          'FROM Customer C JOIN CreditCard CC ON CC.CustomerID=C.CustomerID\n'
          'GROUP BY C.CustomerID, C.FirstName, C.LastName, C.City ORDER BY DeudaTotal DESC LIMIT 3;',
  'explicacion': 'Suma la deuda de todas las tarjetas de cada cliente y se queda con los 3 mayores. WITH '
                 'TIES incluye a un cliente empatado en el tercer puesto, si lo hubiera.'},
 {'n': 5,
  'mision': 'M1',
  'nombre_mision': 'Mapeando el negocio',
  'semana': 'Semanas 6 y 7',
  'pregunta': '¿Qué analistas de riesgo registrados no tienen ninguna investigación asignada?',
  'tecnica': 'Anti-join: LEFT JOIN ... WHERE IS NULL',
  'tablas': ['Analyst', 'Branch', 'Investigation'],
  'tsql': 'SELECT A.AnalystID,\n'
          "       A.AnalystFirstName + ' ' + A.AnalystLastName AS Analista,\n"
          '       B.BranchName,\n'
          '       B.BranchCity,\n'
          '       A.SupervisorID\n'
          'FROM dbo.Analyst            AS A\n'
          'JOIN dbo.Branch             AS B ON B.BranchID  = A.BranchID\n'
          'LEFT JOIN dbo.Investigation AS I ON I.AnalystID = A.AnalystID\n'
          'WHERE I.AnalystID IS NULL\n'
          'ORDER BY A.AnalystID;',
  'lite': "SELECT A.AnalystID, A.AnalystFirstName || ' ' || A.AnalystLastName, B.BranchName, B.BranchCity, "
          'A.SupervisorID\n'
          'FROM Analyst A JOIN Branch B ON B.BranchID=A.BranchID LEFT JOIN Investigation I ON '
          'I.AnalystID=A.AnalystID\n'
          'WHERE I.AnalystID IS NULL ORDER BY A.AnalystID;',
  'explicacion': 'El LEFT JOIN conserva a todos los analistas. Los que no tienen ninguna investigación '
                 'quedan con NULL en las columnas de Investigation y el WHERE los selecciona. Sirve para '
                 'redistribuir la carga de trabajo.'},
 {'n': 6,
  'mision': 'M2',
  'nombre_mision': 'Trazando conexiones',
  'semana': 'Semana 9',
  'pregunta': '¿Cuál es la estructura jerárquica del equipo de riesgo? Mostrar a cada analista con su '
              'sucursal y el código y nombre de su supervisor.',
  'tecnica': 'SELF JOIN (relación recursiva) con LEFT JOIN e ISNULL',
  'tablas': ['Analyst', 'Branch'],
  'tsql': 'SELECT A.AnalystID,\n'
          "       A.AnalystFirstName + ' ' + A.AnalystLastName AS Analista,\n"
          '       B.BranchName,\n'
          '       A.SupervisorID,\n'
          "       ISNULL(S.AnalystFirstName + ' ' + S.AnalystLastName,\n"
          "              'Sin supervisor asignado')          AS Supervisor\n"
          'FROM dbo.Analyst      AS A\n'
          'JOIN dbo.Branch       AS B ON B.BranchID  = A.BranchID\n'
          'LEFT JOIN dbo.Analyst AS S ON S.AnalystID = A.SupervisorID   -- misma tabla, otro rol\n'
          'ORDER BY A.SupervisorID, A.AnalystID;',
  'lite': "SELECT A.AnalystID, A.AnalystFirstName || ' ' || A.AnalystLastName, B.BranchName, "
          'A.SupervisorID,\n'
          "       IFNULL(S.AnalystFirstName || ' ' || S.AnalystLastName,'Sin supervisor asignado')\n"
          'FROM Analyst A JOIN Branch B ON B.BranchID=A.BranchID LEFT JOIN Analyst S ON '
          'S.AnalystID=A.SupervisorID\n'
          'ORDER BY A.SupervisorID, A.AnalystID;',
  'explicacion': 'La tabla Analyst se une consigo misma: el alias A es el analista y S es su supervisor. Con '
                 'LEFT JOIN aparecen también los supervisores y los recién contratados, que tienen '
                 'SupervisorID en NULL.'},
 {'n': 7,
  'mision': 'M2',
  'nombre_mision': 'Trazando conexiones',
  'semana': 'Semana 9',
  'pregunta': '¿Cuál es el detalle completo de las transacciones anómalas investigadas: cliente, tipo de '
              'cuenta, sucursal, monto, analista investigador y dictamen?',
  'tecnica': 'JOIN encadenado de 6 tablas',
  'tablas': ['Customer', 'Account', 'Transaction', 'Branch', 'Investigation', 'Analyst'],
  'tsql': 'SELECT T.TransactionID,\n'
          '       T.TransactionDate,\n'
          "       C.FirstName + ' ' + C.LastName                AS Cliente,\n"
          '       A.AccountType,\n'
          '       B.BranchName,\n'
          '       B.BranchCity,\n'
          '       T.TransactionType,\n'
          '       T.TransactionAmount,\n'
          "       AN.AnalystFirstName + ' ' + AN.AnalystLastName AS AnalistaInvestigador,\n"
          '       I.AssignmentDate,\n'
          '       I.Verdict\n'
          'FROM dbo.[Transaction]   AS T\n'
          'JOIN dbo.Account         AS A  ON A.AccountID      = T.AccountID\n'
          'JOIN dbo.Customer        AS C  ON C.CustomerID     = A.CustomerID\n'
          'JOIN dbo.Branch          AS B  ON B.BranchID       = T.BranchID\n'
          'JOIN dbo.Investigation   AS I  ON I.TransactionID  = T.TransactionID\n'
          'JOIN dbo.Analyst         AS AN ON AN.AnalystID     = I.AnalystID\n'
          'WHERE T.Anomaly = -1\n'
          'ORDER BY T.TransactionID, I.AssignmentDate;',
  'lite': "SELECT T.TransactionID, T.TransactionDate, C.FirstName || ' ' || C.LastName, A.AccountType, "
          'B.BranchName, B.BranchCity,\n'
          "       T.TransactionType, T.TransactionAmount, AN.AnalystFirstName || ' ' || AN.AnalystLastName, "
          'I.AssignmentDate, I.Verdict\n'
          'FROM "Transaction" T JOIN Account A ON A.AccountID=T.AccountID JOIN Customer C ON '
          'C.CustomerID=A.CustomerID\n'
          'JOIN Branch B ON B.BranchID=T.BranchID JOIN Investigation I ON I.TransactionID=T.TransactionID\n'
          'JOIN Analyst AN ON AN.AnalystID=I.AnalystID WHERE T.Anomaly=-1 ORDER BY T.TransactionID, '
          'I.AssignmentDate;',
  'explicacion': 'Recorre toda la cadena del modelo: Customer → Account → Transaction → Branch e '
                 'Investigation → Analyst. Si un caso fue escalado, la transacción aparece una vez por cada '
                 'analista que la revisó.'},
 {'n': 8,
  'mision': 'M2',
  'nombre_mision': 'Trazando conexiones',
  'semana': 'Semana 9',
  'pregunta': '¿Qué sucursales procesan un monto total de transacciones superior al promedio de todas las '
              'sucursales del banco?',
  'tecnica': 'CTE + subconsulta escalar con AVG',
  'tablas': ['Branch', 'Transaction'],
  'tsql': 'WITH TotalSucursal AS (\n'
          '    SELECT B.BranchID,\n'
          '           B.BranchName,\n'
          '           B.BranchCity,\n'
          '           COUNT(T.TransactionID)   AS Operaciones,\n'
          '           SUM(T.TransactionAmount) AS MontoTotal\n'
          '    FROM dbo.Branch        AS B\n'
          '    JOIN dbo.[Transaction] AS T ON T.BranchID = B.BranchID\n'
          '    GROUP BY B.BranchID, B.BranchName, B.BranchCity\n'
          ')\n'
          'SELECT BranchID,\n'
          '       BranchName,\n'
          '       BranchCity,\n'
          '       Operaciones,\n'
          '       MontoTotal,\n'
          '       (SELECT AVG(MontoTotal) FROM TotalSucursal) AS PromedioSucursales\n'
          'FROM TotalSucursal\n'
          'WHERE MontoTotal > (SELECT AVG(MontoTotal) FROM TotalSucursal)\n'
          'ORDER BY MontoTotal DESC;',
  'lite': 'WITH TotalSucursal AS (SELECT B.BranchID, B.BranchName, B.BranchCity, COUNT(T.TransactionID) '
          'Operaciones, SUM(T.TransactionAmount) MontoTotal\n'
          ' FROM Branch B JOIN "Transaction" T ON T.BranchID=B.BranchID GROUP BY B.BranchID, B.BranchName, '
          'B.BranchCity)\n'
          'SELECT BranchID, BranchName, BranchCity, Operaciones, ROUND(MontoTotal,2), ROUND((SELECT '
          'AVG(MontoTotal) FROM TotalSucursal),2)\n'
          'FROM TotalSucursal WHERE MontoTotal > (SELECT AVG(MontoTotal) FROM TotalSucursal) ORDER BY '
          'MontoTotal DESC;',
  'explicacion': 'La CTE calcula el monto total de cada sucursal. La subconsulta saca el promedio de esos '
                 'totales y solo quedan las sucursales que lo superan.'},
 {'n': 9,
  'mision': 'M2',
  'nombre_mision': 'Trazando conexiones',
  'semana': 'Semana 9',
  'pregunta': '¿Qué sucursales no registraron ninguna transacción anómala durante el cuarto trimestre de '
              '2023 (octubre a diciembre)?',
  'tecnica': 'Entidades sin operación en un período: subconsulta correlacionada con NOT EXISTS',
  'tablas': ['Branch', 'Transaction'],
  'tsql': 'SELECT B.BranchID,\n'
          '       B.BranchName,\n'
          '       B.BranchCity\n'
          'FROM dbo.Branch AS B\n'
          'WHERE NOT EXISTS (\n'
          '        SELECT 1\n'
          '        FROM dbo.[Transaction] AS T\n'
          '        WHERE T.BranchID = B.BranchID              -- correlación con la sucursal\n'
          '          AND T.Anomaly = -1\n'
          "          AND T.TransactionDate BETWEEN '2023-10-01' AND '2023-12-31')\n"
          'ORDER BY B.BranchCity, B.BranchName;',
  'lite': 'SELECT B.BranchID, B.BranchName, B.BranchCity FROM Branch B\n'
          'WHERE NOT EXISTS (SELECT 1 FROM "Transaction" T WHERE T.BranchID=B.BranchID AND T.Anomaly=-1 AND '
          "T.TransactionDate BETWEEN '2023-10-01' AND '2023-12-31')\n"
          'ORDER BY B.BranchCity, B.BranchName;',
  'explicacion': 'Para cada sucursal, la subconsulta busca una transacción anómala del cuarto trimestre; NOT '
                 'EXISTS deja solo las sucursales donde no encuentra ninguna. Sirve para saber dónde no se '
                 'detectaron alertas al cierre del año y revisar si el sistema antifraude está funcionando '
                 'en esas sucursales.'},
 {'n': 10,
  'mision': 'M2',
  'nombre_mision': 'Trazando conexiones',
  'semana': 'Semana 9',
  'pregunta': '¿Existen supervisores en los que todos los analistas a su cargo hayan emitido al menos un '
              "dictamen de 'Fraud Confirmed'?",
  'tecnica': 'División relacional: doble NOT EXISTS',
  'tablas': ['Analyst', 'Investigation'],
  'tsql': 'SELECT S.AnalystID                                  AS SupervisorID,\n'
          "       S.AnalystFirstName + ' ' + S.AnalystLastName AS Supervisor,\n"
          '       (SELECT COUNT(*) FROM dbo.Analyst AS A\n'
          '        WHERE A.SupervisorID = S.AnalystID)         AS AnalistasACargo\n'
          'FROM dbo.Analyst AS S\n'
          'WHERE EXISTS (                                      -- es supervisor\n'
          '        SELECT 1 FROM dbo.Analyst AS A\n'
          '        WHERE A.SupervisorID = S.AnalystID)\n'
          '  AND NOT EXISTS (                                  -- no hay subordinado...\n'
          '        SELECT 1\n'
          '        FROM dbo.Analyst AS A\n'
          '        WHERE A.SupervisorID = S.AnalystID\n'
          '          AND NOT EXISTS (                          -- ...sin un fraude confirmado\n'
          '                SELECT 1\n'
          '                FROM dbo.Investigation AS I\n'
          '                WHERE I.AnalystID = A.AnalystID\n'
          "                  AND I.Verdict = 'Fraud Confirmed'));",
  'lite': "SELECT S.AnalystID, S.AnalystFirstName || ' ' || S.AnalystLastName, (SELECT COUNT(*) FROM Analyst "
          'A WHERE A.SupervisorID=S.AnalystID)\n'
          'FROM Analyst S WHERE EXISTS (SELECT 1 FROM Analyst A WHERE A.SupervisorID=S.AnalystID)\n'
          'AND NOT EXISTS (SELECT 1 FROM Analyst A WHERE A.SupervisorID=S.AnalystID\n'
          '  AND NOT EXISTS (SELECT 1 FROM Investigation I WHERE I.AnalystID=A.AnalystID AND '
          "I.Verdict='Fraud Confirmed'));",
  'explicacion': 'Es una división relacional: un supervisor aparece si no existe ningún analista a su cargo '
                 'que no haya confirmado al menos un fraude. Los supervisores con algún analista sin casos '
                 'quedan fuera.'},
 {'n': 11,
  'mision': 'M3',
  'nombre_mision': 'Midiendo el tiempo',
  'semana': 'Semana 10',
  'pregunta': '¿Cuántos días transcurren en promedio entre la fecha de una transacción anómala y la fecha en '
              'que el analista toma el caso, por analista?',
  'tecnica': 'DATEDIFF + AVG por grupo',
  'tablas': ['Investigation', 'Transaction', 'Analyst', 'Branch'],
  'tsql': 'SELECT A.AnalystID,\n'
          "       A.AnalystFirstName + ' ' + A.AnalystLastName AS Analista,\n"
          '       B.BranchName,\n'
          '       COUNT(*) AS CasosAsignados,\n'
          '       AVG(CAST(DATEDIFF(DAY, T.TransactionDate, I.AssignmentDate)\n'
          '                AS DECIMAL(10,2))) AS PromedioDias,\n'
          '       MIN(DATEDIFF(DAY, T.TransactionDate, I.AssignmentDate)) AS MinDias,\n'
          '       MAX(DATEDIFF(DAY, T.TransactionDate, I.AssignmentDate)) AS MaxDias\n'
          'FROM dbo.Investigation AS I\n'
          'JOIN dbo.[Transaction] AS T ON T.TransactionID = I.TransactionID\n'
          'JOIN dbo.Analyst       AS A ON A.AnalystID     = I.AnalystID\n'
          'JOIN dbo.Branch        AS B ON B.BranchID      = A.BranchID\n'
          'GROUP BY A.AnalystID, A.AnalystFirstName, A.AnalystLastName, B.BranchName\n'
          'ORDER BY PromedioDias DESC;',
  'lite': "SELECT A.AnalystID, A.AnalystFirstName || ' ' || A.AnalystLastName, B.BranchName, COUNT(*),\n"
          ' ROUND(AVG(julianday(I.AssignmentDate)-julianday(T.TransactionDate)),2) AS PromedioDias,\n'
          ' MIN(julianday(I.AssignmentDate)-julianday(T.TransactionDate)), '
          'MAX(julianday(I.AssignmentDate)-julianday(T.TransactionDate))\n'
          'FROM Investigation I JOIN "Transaction" T ON T.TransactionID=I.TransactionID JOIN Analyst A ON '
          'A.AnalystID=I.AnalystID\n'
          'JOIN Branch B ON B.BranchID=A.BranchID GROUP BY A.AnalystID, A.AnalystFirstName, '
          'A.AnalystLastName, B.BranchName ORDER BY PromedioDias DESC;',
  'explicacion': 'Se convierte DATEDIFF a DECIMAL antes de promediar porque en SQL Server el AVG de enteros '
                 'devuelve un entero y perdería los decimales. Los supervisores salen con más días porque '
                 'reciben los casos escalados.'},
 {'n': 12,
  'mision': 'M3',
  'nombre_mision': 'Midiendo el tiempo',
  'semana': 'Semana 10',
  'pregunta': '¿Qué clientes tienen tarjetas cuya fecha límite de pago vence en los próximos 7 días (desde '
              'la fecha de corte 20/12/2023) y aún mantienen deuda?',
  'tecnica': 'Vencimientos: DATEADD, DATEDIFF y fecha de referencia',
  'tablas': ['CreditCard', 'Customer'],
  'tsql': "DECLARE @FechaCorte DATE = '2023-12-20';\n"
          '\n'
          'SELECT C.CustomerID,\n'
          "       C.FirstName + ' ' + C.LastName AS Cliente,\n"
          '       C.Email,\n'
          '       CC.CardID,\n'
          '       CC.CardType,\n'
          '       CC.CreditCardBalance,\n'
          '       CC.MinimumPaymentDue,\n'
          '       CC.PaymentDueDate,\n'
          '       DATEDIFF(DAY, @FechaCorte, CC.PaymentDueDate) AS DiasParaVencer\n'
          'FROM dbo.CreditCard AS CC\n'
          'JOIN dbo.Customer   AS C ON C.CustomerID = CC.CustomerID\n'
          'WHERE CC.PaymentDueDate BETWEEN @FechaCorte AND DATEADD(DAY, 7, @FechaCorte)\n'
          '  AND CC.CreditCardBalance > 0\n'
          'ORDER BY DiasParaVencer, CC.CreditCardBalance DESC;',
  'lite': "SELECT C.CustomerID, C.FirstName || ' ' || C.LastName, C.Email, CC.CardID, CC.CardType, "
          'CC.CreditCardBalance, CC.MinimumPaymentDue, CC.PaymentDueDate,\n'
          " CAST(julianday(CC.PaymentDueDate)-julianday('2023-12-20') AS INT) AS DiasParaVencer\n"
          'FROM CreditCard CC JOIN Customer C ON C.CustomerID=CC.CustomerID\n'
          "WHERE CC.PaymentDueDate BETWEEN '2023-12-20' AND date('2023-12-20','+7 day') AND "
          'CC.CreditCardBalance>0\n'
          'ORDER BY DiasParaVencer, CC.CreditCardBalance DESC;',
  'explicacion': 'Se usa una fecha de corte fija porque los datos son de 2023; con GETDATE() la consulta no '
                 'devolvería filas. Sirve para enviar recordatorios de pago antes del vencimiento.'},
 {'n': 13,
  'mision': 'M3',
  'nombre_mision': 'Midiendo el tiempo',
  'semana': 'Semana 10',
  'pregunta': "¿Cómo se clasifica cada cliente ('Alto Valor', 'Estándar', 'Básico') según el monto total de "
              'préstamos que se le ha aprobado?',
  'tecnica': 'CASE con umbrales + LEFT JOIN con filtro en el ON',
  'tablas': ['Customer', 'Loan'],
  'tsql': 'SELECT C.CustomerID,\n'
          "       C.FirstName + ' ' + C.LastName AS Cliente,\n"
          '       ISNULL(SUM(L.LoanAmount), 0)   AS MontoAprobado,\n'
          '       CASE\n'
          "           WHEN SUM(L.LoanAmount) >= 35000 THEN 'Alto Valor'\n"
          "           WHEN SUM(L.LoanAmount) >= 15000 THEN 'Estándar'\n"
          "           WHEN SUM(L.LoanAmount) >  0     THEN 'Básico'\n"
          "           ELSE 'Sin préstamos aprobados'\n"
          '       END AS Segmento\n'
          'FROM dbo.Customer  AS C\n'
          'LEFT JOIN dbo.Loan AS L ON L.CustomerID = C.CustomerID\n'
          "                       AND L.LoanStatus IN ('Approved', 'Closed')  -- Closed: aprobado\n"
          'GROUP BY C.CustomerID, C.FirstName, C.LastName\n'
          'ORDER BY MontoAprobado DESC;',
  'lite': "SELECT C.CustomerID, C.FirstName || ' ' || C.LastName, IFNULL(SUM(L.LoanAmount),0) AS "
          'MontoAprobado,\n'
          " CASE WHEN SUM(L.LoanAmount)>=35000 THEN 'Alto Valor' WHEN SUM(L.LoanAmount)>=15000 THEN "
          "'Estándar' WHEN SUM(L.LoanAmount)>0 THEN 'Básico' ELSE 'Sin préstamos aprobados' END AS Segmento\n"
          'FROM Customer C LEFT JOIN Loan L ON L.CustomerID=C.CustomerID AND L.LoanStatus IN '
          "('Approved','Closed')\n"
          'GROUP BY C.CustomerID, C.FirstName, C.LastName ORDER BY MontoAprobado DESC;',
  'explicacion': 'Se cuentan como aprobados los préstamos Approved y Closed, porque un préstamo cerrado fue '
                 'aprobado antes. El filtro va en el ON del LEFT JOIN para no perder a los clientes que solo '
                 'tienen préstamos rechazados.'},
 {'n': 14,
  'mision': 'M3',
  'nombre_mision': 'Midiendo el tiempo',
  'semana': 'Semana 10',
  'pregunta': '¿Cuántas operaciones de depósito y retiro se ejecutaron exactamente el último día de cada mes '
              '(cierre contable) y cuál fue el total movilizado?',
  'tecnica': 'EOMONTH, FORMAT y agregación condicional',
  'tablas': ['Transaction'],
  'tsql': "SELECT FORMAT(T.TransactionDate, 'yyyy-MM') AS Mes,\n"
          '       EOMONTH(T.TransactionDate)            AS DiaCierre,\n'
          '       COUNT(*)                              AS Operaciones,\n'
          "       SUM(CASE WHEN T.TransactionType = 'Deposit'\n"
          '                THEN T.TransactionAmount ELSE 0 END) AS Depositos,\n'
          "       SUM(CASE WHEN T.TransactionType = 'Withdrawal'\n"
          '                THEN T.TransactionAmount ELSE 0 END) AS Retiros,\n'
          '       SUM(T.TransactionAmount)              AS TotalMovilizado\n'
          'FROM dbo.[Transaction] AS T\n'
          'WHERE T.TransactionDate = EOMONTH(T.TransactionDate)          -- último día del mes\n'
          "  AND T.TransactionType IN ('Deposit', 'Withdrawal')\n"
          "GROUP BY FORMAT(T.TransactionDate, 'yyyy-MM'), EOMONTH(T.TransactionDate)\n"
          'ORDER BY Mes;',
  'lite': "SELECT strftime('%Y-%m',T.TransactionDate) Mes, date(T.TransactionDate,'start of month','+1 "
          "month','-1 day'), COUNT(*),\n"
          " ROUND(SUM(CASE WHEN T.TransactionType='Deposit' THEN T.TransactionAmount ELSE 0 END),2),\n"
          " ROUND(SUM(CASE WHEN T.TransactionType='Withdrawal' THEN T.TransactionAmount ELSE 0 END),2), "
          'ROUND(SUM(T.TransactionAmount),2)\n'
          'FROM "Transaction" T WHERE T.TransactionDate = date(T.TransactionDate,\'start of month\',\'+1 '
          "month','-1 day')\n"
          "AND T.TransactionType IN ('Deposit','Withdrawal') GROUP BY Mes ORDER BY Mes;",
  'explicacion': 'EOMONTH devuelve el último día del mes de cada fecha. Si la fecha de la transacción '
                 'coincide con ese día, la operación ocurrió en el cierre contable.'},
 {'n': 15,
  'mision': 'M3',
  'nombre_mision': 'Midiendo el tiempo',
  'semana': 'Semana 10',
  'pregunta': '¿A qué trimestre pertenece cada registro de feedback de tipo queja o sugerencia y qué '
              'porcentaje se resolvió en cada trimestre?',
  'tecnica': 'DATEPART(QUARTER) y porcentaje con CASE',
  'tablas': ['Feedback'],
  'tsql': 'SELECT YEAR(F.FeedbackDate)              AS Anio,\n'
          '       DATEPART(QUARTER, F.FeedbackDate) AS Trimestre,\n'
          '       F.FeedbackType,\n'
          '       COUNT(*) AS TotalRegistros,\n'
          "       SUM(CASE WHEN F.ResolutionStatus = 'Resolved' THEN 1 ELSE 0 END) AS Resueltos,\n"
          "       CAST(100.0 * SUM(CASE WHEN F.ResolutionStatus = 'Resolved' THEN 1 ELSE 0 END)\n"
          '            / COUNT(*) AS DECIMAL(5,2))  AS PctResuelto\n'
          'FROM dbo.Feedback AS F\n'
          "WHERE F.FeedbackType IN ('Complaint', 'Suggestion')\n"
          'GROUP BY YEAR(F.FeedbackDate), DATEPART(QUARTER, F.FeedbackDate), F.FeedbackType\n'
          'ORDER BY Anio, Trimestre, F.FeedbackType;',
  'lite': "SELECT CAST(strftime('%Y',F.FeedbackDate) AS INT) Anio, (CAST(strftime('%m',F.FeedbackDate) AS "
          'INT)+2)/3 Trimestre, F.FeedbackType, COUNT(*),\n'
          " SUM(CASE WHEN F.ResolutionStatus='Resolved' THEN 1 ELSE 0 END), ROUND(100.0*SUM(CASE WHEN "
          "F.ResolutionStatus='Resolved' THEN 1 ELSE 0 END)/COUNT(*),2)\n"
          "FROM Feedback F WHERE F.FeedbackType IN ('Complaint','Suggestion') GROUP BY Anio, Trimestre, "
          'F.FeedbackType ORDER BY Anio, Trimestre, F.FeedbackType;',
  'explicacion': 'Se multiplica por 100.0 (con decimal) para evitar la división entera. El resultado muestra '
                 'si la atención de quejas mejora o empeora a lo largo del año.'},
 {'n': 16,
  'mision': 'M4',
  'nombre_mision': 'Descubriendo quién lidera',
  'semana': 'Semana 11',
  'pregunta': '¿Cuáles son las 3 transacciones de mayor monto dentro de cada tipo de cuenta (Current vs. '
              'Savings)?',
  'tecnica': 'ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)',
  'tablas': ['Transaction', 'Account', 'Customer'],
  'tsql': 'WITH Ranking AS (\n'
          '    SELECT A.AccountType,\n'
          '           T.TransactionID,\n'
          '           T.TransactionDate,\n'
          '           T.TransactionType,\n'
          '           T.TransactionAmount,\n'
          "           C.FirstName + ' ' + C.LastName AS Cliente,\n"
          '           ROW_NUMBER() OVER (PARTITION BY A.AccountType\n'
          '                              ORDER BY T.TransactionAmount DESC) AS Posicion\n'
          '    FROM dbo.[Transaction] AS T\n'
          '    JOIN dbo.Account       AS A ON A.AccountID  = T.AccountID\n'
          '    JOIN dbo.Customer      AS C ON C.CustomerID = A.CustomerID\n'
          ')\n'
          'SELECT AccountType, Posicion, TransactionID, TransactionDate,\n'
          '       TransactionType, TransactionAmount, Cliente\n'
          'FROM Ranking\n'
          'WHERE Posicion <= 3\n'
          'ORDER BY AccountType, Posicion;',
  'lite': 'WITH Ranking AS (SELECT A.AccountType, T.TransactionID, T.TransactionDate, T.TransactionType, '
          "T.TransactionAmount, C.FirstName || ' ' || C.LastName Cliente,\n"
          ' ROW_NUMBER() OVER (PARTITION BY A.AccountType ORDER BY T.TransactionAmount DESC) Posicion\n'
          ' FROM "Transaction" T JOIN Account A ON A.AccountID=T.AccountID JOIN Customer C ON '
          'C.CustomerID=A.CustomerID)\n'
          'SELECT AccountType, Posicion, TransactionID, TransactionDate, TransactionType, TransactionAmount, '
          'Cliente FROM Ranking WHERE Posicion<=3 ORDER BY AccountType, Posicion;',
  'explicacion': 'PARTITION BY reinicia la numeración en cada tipo de cuenta y el WHERE Posicion <= 3 deja '
                 'el top 3 de cada grupo. ROW_NUMBER no repite números si hay empates; RANK sí lo haría.'},
 {'n': 17,
  'mision': 'M4',
  'nombre_mision': 'Descubriendo quién lidera',
  'semana': 'Semana 11',
  'pregunta': '¿Cuál es el ranking mensual de los analistas de cada sucursal según la cantidad de casos '
              'anómalos cerrados (fraude confirmado o falso positivo)?',
  'tecnica': 'RANK() OVER (PARTITION BY sucursal, mes)',
  'tablas': ['Investigation', 'Analyst', 'Branch'],
  'tsql': 'WITH CasosMes AS (\n'
          '    SELECT B.BranchID,\n'
          '           B.BranchName,\n'
          '           A.AnalystID,\n'
          "           A.AnalystFirstName + ' ' + A.AnalystLastName AS Analista,\n"
          "           FORMAT(I.AssignmentDate, 'yyyy-MM')          AS Mes,\n"
          '           COUNT(*)                                     AS CasosCerrados\n'
          '    FROM dbo.Investigation AS I\n'
          '    JOIN dbo.Analyst       AS A ON A.AnalystID = I.AnalystID\n'
          '    JOIN dbo.Branch        AS B ON B.BranchID  = A.BranchID\n'
          "    WHERE I.Verdict IN ('Fraud Confirmed', 'False Positive')\n"
          '    GROUP BY B.BranchID, B.BranchName, A.AnalystID, A.AnalystFirstName,\n'
          "             A.AnalystLastName, FORMAT(I.AssignmentDate, 'yyyy-MM')\n"
          ')\n'
          'SELECT Mes,\n'
          '       BranchName,\n'
          '       Analista,\n'
          '       CasosCerrados,\n'
          '       RANK() OVER (PARTITION BY BranchID, Mes\n'
          '                    ORDER BY CasosCerrados DESC) AS PuestoEnSucursal\n'
          'FROM CasosMes\n'
          'ORDER BY Mes, BranchName, PuestoEnSucursal;',
  'lite': "WITH CasosMes AS (SELECT B.BranchID, B.BranchName, A.AnalystID, A.AnalystFirstName || ' ' || "
          "A.AnalystLastName Analista, strftime('%Y-%m',I.AssignmentDate) Mes, COUNT(*) CasosCerrados\n"
          ' FROM Investigation I JOIN Analyst A ON A.AnalystID=I.AnalystID JOIN Branch B ON '
          'B.BranchID=A.BranchID\n'
          " WHERE I.Verdict IN ('Fraud Confirmed','False Positive') GROUP BY B.BranchID, B.BranchName, "
          'A.AnalystID, Analista, Mes)\n'
          'SELECT Mes, BranchName, Analista, CasosCerrados, RANK() OVER (PARTITION BY BranchID, Mes ORDER BY '
          'CasosCerrados DESC) PuestoEnSucursal\n'
          'FROM CasosMes ORDER BY Mes, BranchName, PuestoEnSucursal;',
  'explicacion': 'Primero se cuentan los casos cerrados por analista y mes; después RANK ordena a los '
                 'analistas dentro de cada sucursal y mes. Si dos analistas empatan, comparten el mismo '
                 'puesto.'},
 {'n': 18,
  'mision': 'M4',
  'nombre_mision': 'Descubriendo quién lidera',
  'semana': 'Semana 11',
  'pregunta': '¿Cómo varió (en valor neto y en porcentaje) el monto de préstamos aprobados de cada mes '
              'respecto al mes inmediatamente anterior?',
  'tecnica': 'LAG() OVER (ORDER BY mes)',
  'tablas': ['Loan'],
  'tsql': 'WITH PrestamosMes AS (\n'
          "    SELECT FORMAT(L.ApprovalRejectionDate, 'yyyy-MM') AS Mes,\n"
          '           COUNT(*)          AS PrestamosAprobados,\n'
          '           SUM(L.LoanAmount) AS MontoAprobado\n'
          '    FROM dbo.Loan AS L\n'
          "    WHERE L.LoanStatus IN ('Approved', 'Closed')\n"
          "    GROUP BY FORMAT(L.ApprovalRejectionDate, 'yyyy-MM')\n"
          ')\n'
          'SELECT Mes,\n'
          '       PrestamosAprobados,\n'
          '       MontoAprobado,\n'
          '       LAG(MontoAprobado) OVER (ORDER BY Mes)                 AS MontoMesAnterior,\n'
          '       MontoAprobado - LAG(MontoAprobado) OVER (ORDER BY Mes) AS VariacionNeta,\n'
          '       CAST(100.0 * (MontoAprobado - LAG(MontoAprobado) OVER (ORDER BY Mes))\n'
          '            / NULLIF(LAG(MontoAprobado) OVER (ORDER BY Mes), 0)\n'
          '            AS DECIMAL(10,2))                                 AS PctVariacion\n'
          'FROM PrestamosMes\n'
          'ORDER BY Mes;',
  'lite': "WITH PrestamosMes AS (SELECT strftime('%Y-%m',L.ApprovalRejectionDate) Mes, COUNT(*) "
          'PrestamosAprobados, SUM(L.LoanAmount) MontoAprobado\n'
          " FROM Loan L WHERE L.LoanStatus IN ('Approved','Closed') GROUP BY Mes)\n"
          'SELECT Mes, PrestamosAprobados, ROUND(MontoAprobado,2), ROUND(LAG(MontoAprobado) OVER (ORDER BY '
          'Mes),2), ROUND(MontoAprobado-LAG(MontoAprobado) OVER (ORDER BY Mes),2),\n'
          ' ROUND(100.0*(MontoAprobado-LAG(MontoAprobado) OVER (ORDER BY Mes))/NULLIF(LAG(MontoAprobado) '
          'OVER (ORDER BY Mes),0),2) FROM PrestamosMes ORDER BY Mes;',
  'explicacion': 'LAG trae el monto del mes anterior a la misma fila para poder restarlo. NULLIF evita '
                 'dividir entre cero. El primer mes sale con NULL porque no tiene un mes anterior.'},
 {'n': 19,
  'mision': 'M4',
  'nombre_mision': 'Descubriendo quién lidera',
  'semana': 'Semana 11',
  'pregunta': '¿Cuál es el monto acumulado (running total) de transacciones de la sucursal principal, día a '
              'día, en el año y dentro de cada mes?',
  'tecnica': 'SUM() OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)',
  'tablas': ['Transaction', 'Branch'],
  'tsql': 'WITH SucursalPrincipal AS (           -- sucursal con mayor monto transaccionado\n'
          '    SELECT TOP 1 T.BranchID\n'
          '    FROM dbo.[Transaction] AS T\n'
          '    GROUP BY T.BranchID\n'
          '    ORDER BY SUM(T.TransactionAmount) DESC\n'
          '),\n'
          'Diario AS (\n'
          '    SELECT B.BranchName,\n'
          '           T.TransactionDate        AS Fecha,\n'
          '           COUNT(*)                 AS Operaciones,\n'
          '           SUM(T.TransactionAmount) AS MontoDia\n'
          '    FROM dbo.[Transaction] AS T\n'
          '    JOIN dbo.Branch        AS B ON B.BranchID = T.BranchID\n'
          '    WHERE T.BranchID = (SELECT BranchID FROM SucursalPrincipal)\n'
          '    GROUP BY B.BranchName, T.TransactionDate\n'
          ')\n'
          'SELECT BranchName,\n'
          '       Fecha,\n'
          '       Operaciones,\n'
          '       MontoDia,\n'
          '       SUM(MontoDia) OVER (ORDER BY Fecha\n'
          '           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS AcumuladoAnual,\n'
          '       SUM(MontoDia) OVER (PARTITION BY YEAR(Fecha), MONTH(Fecha) ORDER BY Fecha\n'
          '           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS AcumuladoDelMes\n'
          'FROM Diario\n'
          'ORDER BY Fecha;',
  'lite': 'WITH SucursalPrincipal AS (SELECT T.BranchID FROM "Transaction" T GROUP BY T.BranchID ORDER BY '
          'SUM(T.TransactionAmount) DESC LIMIT 1),\n'
          'Diario AS (SELECT B.BranchName, T.TransactionDate Fecha, COUNT(*) Operaciones, '
          'SUM(T.TransactionAmount) MontoDia\n'
          ' FROM "Transaction" T JOIN Branch B ON B.BranchID=T.BranchID WHERE T.BranchID=(SELECT BranchID '
          'FROM SucursalPrincipal) GROUP BY B.BranchName, T.TransactionDate)\n'
          'SELECT BranchName, Fecha, Operaciones, ROUND(MontoDia,2), ROUND(SUM(MontoDia) OVER (ORDER BY '
          'Fecha ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),2),\n'
          " ROUND(SUM(MontoDia) OVER (PARTITION BY strftime('%Y-%m',Fecha) ORDER BY Fecha ROWS BETWEEN "
          'UNBOUNDED PRECEDING AND CURRENT ROW),2) FROM Diario ORDER BY Fecha;',
  'explicacion': "La 'sucursal principal' se define como la de mayor monto transaccionado. El primer "
                 'acumulado suma desde el inicio del año; el segundo vuelve a cero el primer día de cada mes '
                 'porque está particionado por año y mes.'},
 {'n': 20,
  'mision': 'M4',
  'nombre_mision': 'Descubriendo quién lidera',
  'semana': 'Semana 11',
  'pregunta': '¿Qué porcentaje del saldo total de deuda en tarjetas de crédito del banco representa cada '
              'marca (Visa, MasterCard, AMEX)?',
  'tecnica': 'SUM() OVER () para % de participación',
  'tablas': ['CreditCard'],
  'tsql': 'SELECT CC.CardType,\n'
          '       COUNT(*)                                AS Tarjetas,\n'
          '       SUM(CC.CreditCardBalance)               AS DeudaMarca,\n'
          '       SUM(SUM(CC.CreditCardBalance)) OVER ()  AS DeudaTotalBanco,\n'
          '       CAST(100.0 * SUM(CC.CreditCardBalance)\n'
          '            / SUM(SUM(CC.CreditCardBalance)) OVER ()\n'
          '            AS DECIMAL(5,2))                   AS PctParticipacion\n'
          'FROM dbo.CreditCard AS CC\n'
          'GROUP BY CC.CardType\n'
          'ORDER BY PctParticipacion DESC;',
  'lite': 'SELECT CC.CardType, COUNT(*), ROUND(SUM(CC.CreditCardBalance),2), '
          'ROUND(SUM(SUM(CC.CreditCardBalance)) OVER (),2),\n'
          ' ROUND(100.0*SUM(CC.CreditCardBalance)/SUM(SUM(CC.CreditCardBalance)) OVER (),2) Pct FROM '
          'CreditCard CC GROUP BY CC.CardType ORDER BY Pct DESC;',
  'explicacion': 'El SUM interno suma la deuda de cada marca; el SUM ... OVER () externo suma esas tres '
                 'cifras y da el total del banco sin colapsar las filas. Los porcentajes suman 100 %.'},
 {'n': 21,
  'mision': 'M5',
  'nombre_mision': 'Construyendo el reporte',
  'semana': 'Semana 13',
  'pregunta': '¿Cuál fue el monto transaccionado en 2023 por ciudad de sucursal (filas) y trimestre '
              '(columnas Q1 a Q4), incluyendo el total anual?',
  'tecnica': 'PIVOT estático con CHOOSE(DATEPART(QUARTER)) y total en el SELECT exterior',
  'tablas': ['Transaction', 'Branch'],
  'tsql': 'SELECT BranchCity,\n'
          '       ISNULL([Q1], 0) AS Q1,\n'
          '       ISNULL([Q2], 0) AS Q2,\n'
          '       ISNULL([Q3], 0) AS Q3,\n'
          '       ISNULL([Q4], 0) AS Q4,\n'
          '       ISNULL([Q1], 0) + ISNULL([Q2], 0)\n'
          '     + ISNULL([Q3], 0) + ISNULL([Q4], 0) AS TotalAnio\n'
          'FROM (\n'
          '    SELECT B.BranchCity,\n'
          '           CHOOSE(DATEPART(QUARTER, T.TransactionDate),\n'
          "                  'Q1', 'Q2', 'Q3', 'Q4') AS Trimestre,\n"
          '           T.TransactionAmount\n'
          '    FROM dbo.[Transaction] AS T\n'
          '    JOIN dbo.Branch        AS B ON B.BranchID = T.BranchID\n'
          '    WHERE YEAR(T.TransactionDate) = 2023\n'
          ') AS Origen\n'
          'PIVOT (\n'
          '    SUM(TransactionAmount)\n'
          '    FOR Trimestre IN ([Q1], [Q2], [Q3], [Q4])\n'
          ') AS Pvt\n'
          'ORDER BY TotalAnio DESC;',
  'lite': 'SELECT B.BranchCity,\n'
          " ROUND(SUM(CASE WHEN (CAST(strftime('%m',T.TransactionDate) AS INT)+2)/3=1 THEN "
          'T.TransactionAmount ELSE 0 END),2) Q1,\n'
          " ROUND(SUM(CASE WHEN (CAST(strftime('%m',T.TransactionDate) AS INT)+2)/3=2 THEN "
          'T.TransactionAmount ELSE 0 END),2) Q2,\n'
          " ROUND(SUM(CASE WHEN (CAST(strftime('%m',T.TransactionDate) AS INT)+2)/3=3 THEN "
          'T.TransactionAmount ELSE 0 END),2) Q3,\n'
          " ROUND(SUM(CASE WHEN (CAST(strftime('%m',T.TransactionDate) AS INT)+2)/3=4 THEN "
          'T.TransactionAmount ELSE 0 END),2) Q4,\n'
          ' ROUND(SUM(T.TransactionAmount),2) TotalAnio\n'
          'FROM "Transaction" T JOIN Branch B ON B.BranchID=T.BranchID WHERE '
          "strftime('%Y',T.TransactionDate)='2023'\n"
          'GROUP BY B.BranchCity ORDER BY TotalAnio DESC;',
  'explicacion': 'CHOOSE convierte el número de trimestre en la etiqueta Q1 a Q4, y PIVOT convierte esas '
                 'etiquetas en columnas. ISNULL pone 0 en un trimestre sin operaciones. El total anual se '
                 'calcula en el SELECT exterior porque no puede ir dentro del PIVOT.'},
 {'n': 22,
  'mision': 'M5',
  'nombre_mision': 'Construyendo el reporte',
  'semana': 'Semana 13',
  'pregunta': '¿Cuál es la deuda total en tarjetas de crédito por ciudad del cliente (filas) y marca de '
              'tarjeta (columnas), generando las columnas automáticamente desde los datos?',
  'tecnica': 'PIVOT dinámico: STRING_AGG(QUOTENAME) + SQL dinámico con sp_executesql',
  'tablas': ['CreditCard', 'Customer'],
  'tsql': 'DECLARE @cols  NVARCHAR(MAX);\n'
          'DECLARE @query NVARCHAR(MAX);\n'
          '\n'
          '-- Paso 1: lista de marcas como columnas: [AMEX], [MasterCard], [Visa]\n'
          "SELECT @cols = STRING_AGG(QUOTENAME(CardType), ', ')\n"
          'FROM (SELECT DISTINCT CardType FROM dbo.CreditCard) AS T;\n'
          '\n'
          '-- Paso 2: construir el PIVOT como texto\n'
          "SET @query = N'\n"
          "SELECT City, ' + @cols + N'\n"
          'FROM (\n'
          '    SELECT C.City, CC.CardType, CC.CreditCardBalance\n'
          '    FROM dbo.CreditCard AS CC\n'
          '    JOIN dbo.Customer   AS C ON C.CustomerID = CC.CustomerID\n'
          ') AS Origen\n'
          'PIVOT (\n'
          '    SUM(CreditCardBalance)\n'
          "    FOR CardType IN (' + @cols + N')\n"
          ') AS Pvt\n'
          "ORDER BY City;';\n"
          '\n'
          '-- Paso 3: ejecutar el SQL generado\n'
          'EXEC sp_executesql @query;',
  'lite': 'SELECT C.City,\n'
          " ROUND(SUM(CASE WHEN CC.CardType='AMEX' THEN CC.CreditCardBalance END),2) AMEX,\n"
          " ROUND(SUM(CASE WHEN CC.CardType='MasterCard' THEN CC.CreditCardBalance END),2) MasterCard,\n"
          " ROUND(SUM(CASE WHEN CC.CardType='Visa' THEN CC.CreditCardBalance END),2) Visa\n"
          'FROM CreditCard CC JOIN Customer C ON C.CustomerID=CC.CustomerID GROUP BY C.City ORDER BY C.City;',
  'explicacion': 'Las marcas no se escriben a mano: STRING_AGG con QUOTENAME arma la lista [AMEX], '
                 '[MasterCard], [Visa] a partir de los datos. Si el banco agrega una marca nueva, la '
                 'consulta la muestra sin cambiar el código. sp_executesql ejecuta el texto armado en '
                 '@query.'},
 {'n': 23,
  'mision': 'M5',
  'nombre_mision': 'Construyendo el reporte',
  'semana': 'Semana 13',
  'pregunta': '¿Cuánto monto acumula cada ciudad de sucursal en el año (YTD), en el trimestre (QTD) y en el '
              'mes (MTD) a la fecha de corte del 20/12/2023?',
  'tecnica': 'Análisis temporal YTD/QTD/MTD con SUM(CASE WHEN ... BETWEEN) y DATEFROMPARTS',
  'tablas': ['Transaction', 'Branch'],
  'tsql': "DECLARE @Ref       DATE = '2023-12-20';\n"
          'DECLARE @InicioYTD DATE = DATEFROMPARTS(YEAR(@Ref), 1, 1);\n'
          'DECLARE @InicioMTD DATE = DATEFROMPARTS(YEAR(@Ref), MONTH(@Ref), 1);\n'
          'DECLARE @InicioQTD DATE = DATEADD(QUARTER, DATEDIFF(QUARTER, 0, @Ref), 0);\n'
          '\n'
          'SELECT B.BranchCity,\n'
          '       SUM(CASE WHEN T.TransactionDate BETWEEN @InicioYTD AND @Ref\n'
          '                THEN T.TransactionAmount ELSE 0 END) AS MontoYTD,\n'
          '       SUM(CASE WHEN T.TransactionDate BETWEEN @InicioQTD AND @Ref\n'
          '                THEN T.TransactionAmount ELSE 0 END) AS MontoQTD,\n'
          '       SUM(CASE WHEN T.TransactionDate BETWEEN @InicioMTD AND @Ref\n'
          '                THEN T.TransactionAmount ELSE 0 END) AS MontoMTD\n'
          'FROM dbo.[Transaction] AS T\n'
          'JOIN dbo.Branch        AS B ON B.BranchID = T.BranchID\n'
          'GROUP BY B.BranchCity\n'
          'ORDER BY MontoYTD DESC;',
  'lite': 'SELECT B.BranchCity,\n'
          " ROUND(SUM(CASE WHEN T.TransactionDate BETWEEN '2023-01-01' AND '2023-12-20' THEN "
          'T.TransactionAmount ELSE 0 END),2) MontoYTD,\n'
          " ROUND(SUM(CASE WHEN T.TransactionDate BETWEEN '2023-10-01' AND '2023-12-20' THEN "
          'T.TransactionAmount ELSE 0 END),2) MontoQTD,\n'
          " ROUND(SUM(CASE WHEN T.TransactionDate BETWEEN '2023-12-01' AND '2023-12-20' THEN "
          'T.TransactionAmount ELSE 0 END),2) MontoMTD\n'
          'FROM "Transaction" T JOIN Branch B ON B.BranchID=T.BranchID GROUP BY B.BranchCity ORDER BY '
          'MontoYTD DESC;',
  'explicacion': 'Cada columna suma solo las transacciones que caen en su rango: desde el 1 de enero (YTD), '
                 'desde el inicio del trimestre (QTD) o desde el día 1 del mes (MTD), hasta la fecha de '
                 'corte. Si se cambia @Ref, los tres horizontes se recalculan solos.'},
 {'n': 24,
  'mision': 'M5',
  'nombre_mision': 'Construyendo el reporte',
  'semana': 'Semana 13',
  'pregunta': '¿Cómo creció el monto de préstamos aprobados de cada tipo entre 2020, 2021 y 2022, comparando '
              'el mismo corte del año (1 de enero al 30 de junio)?',
  'tecnica': 'PIVOT por año + YTD interanual con corte comparable (MONTH/DAY)',
  'tablas': ['Loan'],
  'tsql': 'DECLARE @RefMes INT = 6;    -- hasta junio\n'
          'DECLARE @RefDia INT = 30;   -- día 30\n'
          '\n'
          'SELECT LoanType,\n'
          '       ISNULL([2020], 0) AS YTD_2020,\n'
          '       ISNULL([2021], 0) AS YTD_2021,\n'
          '       ISNULL([2022], 0) AS YTD_2022,\n'
          '       CAST(100.0 * (ISNULL([2022], 0) - ISNULL([2021], 0))\n'
          '            / NULLIF([2021], 0) AS DECIMAL(6,2)) AS PctCrec_2022_vs_2021\n'
          'FROM (\n'
          '    SELECT L.LoanType,\n'
          '           YEAR(L.ApprovalRejectionDate) AS Anio,\n'
          '           L.LoanAmount\n'
          '    FROM dbo.Loan AS L\n'
          "    WHERE L.LoanStatus IN ('Approved', 'Closed')\n"
          '      AND (MONTH(L.ApprovalRejectionDate) < @RefMes\n'
          '           OR (MONTH(L.ApprovalRejectionDate) = @RefMes\n'
          '               AND DAY(L.ApprovalRejectionDate) <= @RefDia))\n'
          ') AS Origen\n'
          'PIVOT (\n'
          '    SUM(LoanAmount)\n'
          '    FOR Anio IN ([2020], [2021], [2022])\n'
          ') AS Pvt\n'
          'ORDER BY YTD_2022 DESC;',
  'lite': "WITH O AS (SELECT LoanType, CAST(strftime('%Y',ApprovalRejectionDate) AS INT) Anio, LoanAmount "
          'FROM Loan\n'
          " WHERE LoanStatus IN ('Approved','Closed') AND CAST(strftime('%m',ApprovalRejectionDate) AS INT) "
          '<= 6),\n'
          'P AS (SELECT LoanType, SUM(CASE WHEN Anio=2020 THEN LoanAmount ELSE 0 END) Y20, SUM(CASE WHEN '
          'Anio=2021 THEN LoanAmount ELSE 0 END) Y21,\n'
          ' SUM(CASE WHEN Anio=2022 THEN LoanAmount ELSE 0 END) Y22 FROM O GROUP BY LoanType)\n'
          'SELECT LoanType, ROUND(Y20,2), ROUND(Y21,2), ROUND(Y22,2), ROUND(100.0*(Y22-Y21)/NULLIF(Y21,0),2) '
          'FROM P ORDER BY Y22 DESC;',
  'explicacion': 'El filtro (mes < 6) OR (mes = 6 AND día <= 30) aplica el mismo corte en los tres años, así '
                 'la comparación es justa. PIVOT pone cada año en una columna y el SELECT exterior calcula '
                 'el crecimiento de 2022 frente a 2021.'},
 {'n': 25,
  'mision': 'M5',
  'nombre_mision': 'Construyendo el reporte',
  'semana': 'Semana 13',
  'pregunta': '¿Cuánto se cumplió de la meta trimestral de monto transaccionado de 2023 por tipo de '
              'operación (depósito, retiro, transferencia), si las metas están registradas en columnas Q1 a '
              'Q4?',
  'tecnica': "UNPIVOT + tabla en memoria con VALUES + CTE encadenadas + LEFT JOIN + FORMAT('P1')",
  'tablas': ['Transaction'],
  'tsql': 'WITH Meta AS (                     -- Paso 1: metas en columnas (tabla en memoria)\n'
          '    SELECT * FROM (VALUES\n'
          "        ('Deposit',    1000000.0, 1050000.0, 1100000.0, 1100000.0),\n"
          "        ('Withdrawal', 1050000.0, 1050000.0, 1050000.0, 1050000.0),\n"
          "        ('Transfer',   1050000.0, 1000000.0, 1050000.0, 1050000.0)\n"
          '    ) AS T(TipoOperacion, Q1, Q2, Q3, Q4)\n'
          '),\n'
          'MetaNormalizada AS (               -- Paso 2: UNPIVOT, columnas Q1..Q4 a filas\n'
          '    SELECT TipoOperacion, Trimestre, Meta\n'
          '    FROM Meta\n'
          '    UNPIVOT (Meta FOR Trimestre IN ([Q1], [Q2], [Q3], [Q4])) AS U\n'
          '),\n'
          'EjecutadoReal AS (                 -- Paso 3: monto real por tipo y trimestre\n'
          '    SELECT T.TransactionType AS TipoOperacion,\n'
          '           CHOOSE(DATEPART(QUARTER, T.TransactionDate),\n'
          "                  'Q1', 'Q2', 'Q3', 'Q4') AS Trimestre,\n"
          '           SUM(T.TransactionAmount) AS Ejecutado\n'
          '    FROM dbo.[Transaction] AS T\n'
          '    WHERE YEAR(T.TransactionDate) = 2023\n'
          '    GROUP BY T.TransactionType,\n'
          '             CHOOSE(DATEPART(QUARTER, T.TransactionDate),\n'
          "                    'Q1', 'Q2', 'Q3', 'Q4')\n"
          ')\n'
          'SELECT M.TipoOperacion,                -- Paso 4: meta vs. ejecutado\n'
          '       M.Trimestre,\n'
          '       M.Meta,\n'
          '       ISNULL(E.Ejecutado, 0)          AS Ejecutado,\n'
          '       ISNULL(E.Ejecutado, 0) - M.Meta AS Diferencia,\n'
          "       FORMAT(ISNULL(E.Ejecutado, 0) / M.Meta, 'P1', 'en-US') AS PctCumplimiento\n"
          'FROM MetaNormalizada AS M\n'
          'LEFT JOIN EjecutadoReal AS E ON E.TipoOperacion = M.TipoOperacion\n'
          '                            AND E.Trimestre     = M.Trimestre\n'
          'ORDER BY M.TipoOperacion, M.Trimestre;',
  'lite': 'WITH M AS (\n'
          " SELECT 'Deposit' T,'Q1' Q,1000000.0 Meta UNION ALL SELECT 'Deposit','Q2',1050000.0 UNION ALL "
          "SELECT 'Deposit','Q3',1100000.0 UNION ALL SELECT 'Deposit','Q4',1100000.0\n"
          " UNION ALL SELECT 'Withdrawal','Q1',1050000.0 UNION ALL SELECT 'Withdrawal','Q2',1050000.0 UNION "
          "ALL SELECT 'Withdrawal','Q3',1050000.0 UNION ALL SELECT 'Withdrawal','Q4',1050000.0\n"
          " UNION ALL SELECT 'Transfer','Q1',1050000.0 UNION ALL SELECT 'Transfer','Q2',1000000.0 UNION ALL "
          "SELECT 'Transfer','Q3',1050000.0 UNION ALL SELECT 'Transfer','Q4',1050000.0),\n"
          "E AS (SELECT TransactionType T, 'Q'||((CAST(strftime('%m',TransactionDate) AS INT)+2)/3) Q, "
          'SUM(TransactionAmount) Ej FROM "Transaction"\n'
          " WHERE strftime('%Y',TransactionDate)='2023' GROUP BY 1,2)\n"
          'SELECT M.T, M.Q, M.Meta, ROUND(IFNULL(E.Ej,0),2), ROUND(IFNULL(E.Ej,0)-M.Meta,2), '
          "ROUND(100.0*IFNULL(E.Ej,0)/M.Meta,1)||'%'\n"
          'FROM M LEFT JOIN E ON E.T=M.T AND E.Q=M.Q ORDER BY M.T, M.Q;',
  'explicacion': 'La tabla en memoria (VALUES) simula cómo Finanzas guarda las metas: una columna por '
                 'trimestre. UNPIVOT las pasa a filas para poder unirlas con lo ejecutado, que se calcula '
                 "por tipo y trimestre. FORMAT con 'P1' muestra el cumplimiento como porcentaje con un "
                 'decimal.'}]
