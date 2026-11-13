# BancoVigía · Aplicativo de monitoreo 360° (Streamlit + SQL Server)

Grupo 8 · Ingeniería de Datos · Sección C

## 1. Preparar la base de datos en SQL Server

En SQL Server Management Studio, ejecutar en este orden (carpeta `sql`):

1. `01_BancoVigia_3FN.sql`: crea la base `BancoVigia` con las 9 tablas en 3FN y carga los datos.
2. `03_Vistas_Funcion_Procedimientos.sql`: crea las vistas, la función `fn_SeveridadFraude` y los
   procedimientos `sp_DesempenoAnalistas` y `sp_PerfilCliente360`, que usa el aplicativo.

(`02_Consultas_Misiones.sql` contiene las 25 consultas; no es necesario para el aplicativo.)

## 2. Instalar las librerías de Python (una sola vez)

Abrir **Anaconda Prompt**, ubicarse en esta carpeta y ejecutar:

```
pip install -r requirements.txt
```

Para conectarse a SQL Server también se necesita el **ODBC Driver 17 o 18 for SQL Server**
(normalmente ya viene instalado con SQL Server / SSMS).

## 3. Abrir el aplicativo

```
streamlit run app.py
```

o doble clic en `ejecutar_app.bat`. Se abre en el navegador (http://localhost:8501).

En la barra lateral, en **Conexión a la base de datos**, escribir el nombre del servidor
(por ejemplo `localhost` o `.\SQLEXPRESS`, el mismo que aparece al abrir SSMS) y pulsar **Conectar**.

Si SQL Server no está disponible, el aplicativo usa automáticamente la **base demo**
(`data/BancoVigia_demo.db`, SQLite) con los mismos datos, para poder presentarlo igual.
Para regenerarla: `python crear_demo_db.py`.

## 4. Páginas

| Página | Qué muestra | Objetos SQL que usa |
|---|---|---|
| Resumen ejecutivo | KPIs, tendencia mensual, operaciones por tipo y cuenta | vw_TransaccionDetalle, vw_InvestigacionDetalle |
| Monitoreo de fraude | Alertas por ciudad, mapa de calor ciudad × trimestre, dictámenes, severidad | vistas + fn_SeveridadFraude |
| Equipo de riesgo | Productividad por analista con filtros y jerarquía de supervisión | sp_DesempenoAnalistas, Analyst (self join) |
| Perfil 360° del cliente | Ficha completa de un cliente: cuentas, transacciones, préstamos, tarjetas, atención | sp_PerfilCliente360, vw_PerfilCliente360 |
| Cartera y atención | Préstamos con variación mensual, deuda por marca, vencimientos, atención al cliente | Loan, CreditCard, Feedback |
| Consultas SQL (misiones) | Las 25 consultas con su código y ejecución en vivo | 9 tablas |
| Modelo de datos | Diagrama relacional y conteo de registros | 9 tablas |

## 5. Archivos

- `app.py`: interfaz en Streamlit.
- `db.py`: conexión a SQL Server (pyodbc) y modo demo.
- `reportes.py`: gráficos (matplotlib y seaborn).
- `consultas_misiones.py`: las 25 consultas de las misiones.
- `crear_demo_db.py` y `data/`: base demo en SQLite y CSV normalizados.
