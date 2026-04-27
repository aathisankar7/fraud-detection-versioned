import duckdb
con=duckdb.connect("fraud_v2.duckdb")
con.execute("""
CREATE OR REPLACE TABLE advanced_customer_profile AS

WITH base AS (
    SELECT *
    FROM 'data/transactions_v2.csv'
),

top_city_ranked AS (
    SELECT
        account_id,
        city,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM base
    GROUP BY account_id, city
),

top_type_ranked AS (
    SELECT
        account_id,
        txn_type,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (
            PARTITION BY account_id
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM base
    GROUP BY account_id, txn_type
),

main_profile AS (
    SELECT
        account_id,
        MEDIAN(amount) AS median_txn_amt,
        SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
        SUM(
            CASE
                WHEN EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP)) BETWEEN 0 AND 5
                THEN 1 ELSE 0
            END
        ) AS night_txn_count,
        SUM(
            CASE
                WHEN EXTRACT(DAYOFWEEK FROM CAST(timestamp AS TIMESTAMP)) IN (0,6)
                THEN 1 ELSE 0
            END
        ) AS weekend_txn_count
    FROM base
    GROUP BY account_id
)

SELECT
    m.account_id,
    ROUND(m.median_txn_amt,2) AS median_txn_amt,
    c.city AS top_city,
    t.txn_type AS top_txn_type,
    m.fraud_count,
    m.night_txn_count,
    m.weekend_txn_count
FROM main_profile m
LEFT JOIN top_city_ranked c
    ON m.account_id = c.account_id
   AND c.rn = 1
LEFT JOIN top_type_ranked t
    ON m.account_id = t.account_id
   AND t.rn = 1
""")
print("advanced_customer_profiling completed")
result=con.execute("""select * from advanced_customer_profile
limit 5""").fetchall()
print(result)
con.close()
