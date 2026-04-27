import duckdb

con = duckdb.connect("fraud.duckdb")

con.execute("""
CREATE OR REPLACE TABLE fraud_model_input AS
SELECT
    t.account_id,
    t.amount,
    t.city,
    t.txn_type,
    t.channel,
    t.device_id,
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
    ap.weekend_txn_count

FROM 'data/transactions.csv' t

LEFT JOIN customer_profile cp
    ON t.account_id = cp.account_id

LEFT JOIN advanced_customer_profile ap
    ON t.account_id = ap.account_id
""")

print("fraud_model_input created")

rows = con.execute("""
SELECT * FROM fraud_model_input
LIMIT 5
""").fetchall()

print(rows)

con.close()
print("done")