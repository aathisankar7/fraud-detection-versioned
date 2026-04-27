import duckdb

con = duckdb.connect("fraud_v2.duckdb")

con.execute("""
CREATE OR REPLACE TABLE fraud_model_input_v3 AS

SELECT

    t.account_id,
    t.amount,
    t.txn_type,
    t.city,
    t.channel,
    t.device_id,
    t.balance_before,
    t.balance_after,
    t.is_fraud,

    cp.tot_txn,
    cp.avg_txn_amt,
    cp.max_txn_amount,
    cp.total_spend,
    cp.distinct_devices,

    ap.median_txn_amt,
    ap.top_city,
    ap.top_txn_type,
    ap.fraud_count,
    ap.night_txn_count,
    ap.weekend_txn_count,

    ROUND(t.amount / NULLIF(cp.avg_txn_amt,0),2) AS amt_vs_avg,

    ROUND(t.amount / NULLIF(ap.median_txn_amt,0),2) AS amt_vs_median,

    CASE
        WHEN t.city = ap.top_city THEN 1
        ELSE 0
    END AS city_match,

    ROUND(t.amount / NULLIF(t.balance_before,0),2) AS amt_vs_balance,

    CASE
        WHEN CAST(REPLACE(t.device_id,'DEV','') AS INTEGER) >= 9000
        THEN 1
        ELSE 0
    END AS device_risk_flag,

    CASE
        WHEN t.balance_after <= 500
        THEN 1
        ELSE 0
    END AS balance_low_flag

FROM 'data/transactions_v2.csv' t

LEFT JOIN customer_profile cp
    ON t.account_id = cp.account_id

LEFT JOIN advanced_customer_profile ap
    ON t.account_id = ap.account_id
""")

print("fraud_model_input_v3 upgraded created")

print(
con.execute("""
SELECT * FROM fraud_model_input_v3
LIMIT 10
""").fetchall()
)

con.close()
print("done")