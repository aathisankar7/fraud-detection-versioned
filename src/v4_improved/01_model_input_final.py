import duckdb

con = duckdb.connect("fraud_v2.duckdb")

con.execute("""
CREATE OR REPLACE TABLE fraud_model_input_final AS

WITH txn_base AS (
    SELECT *,
        LAG(amount) OVER (PARTITION BY account_id ORDER BY timestamp) AS prev_amount,
        LAG(CAST(timestamp AS TIMESTAMP)) OVER (
            PARTITION BY account_id ORDER BY timestamp
        ) AS prev_ts,
        EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP)) AS txn_hour,
        EXTRACT(DAYOFWEEK FROM CAST(timestamp AS TIMESTAMP)) AS txn_dow,
        ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY timestamp) AS txn_seq
    FROM 'data/transactions_v2.csv'
),

std_table AS (
    SELECT account_id,
        ROUND(STDDEV(amount),2) AS std_amt
    FROM 'data/transactions_v2.csv'
    GROUP BY account_id
),

features AS (
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

    COALESCE(ROUND(t.amount / NULLIF(cp.avg_txn_amt,0),2), 0) AS amt_vs_avg,

    COALESCE(ROUND(t.amount / NULLIF(ap.median_txn_amt,0),2), 0) AS amt_vs_median,

    CASE
        WHEN t.city = ap.top_city THEN 1
        ELSE 0
    END AS city_match,

    COALESCE(ROUND(t.amount / NULLIF(t.balance_before,0),2), 0) AS amt_vs_balance,

    CASE
        WHEN CAST(REPLACE(t.device_id,'DEV','') AS INTEGER) >= 9000
        THEN 1
        ELSE 0
    END AS device_risk_flag,

    CASE
        WHEN t.balance_after <= 500
        THEN 1
        ELSE 0
    END AS balance_low_flag,

    t.txn_hour,

    t.txn_dow,

    CASE
        WHEN t.txn_hour BETWEEN 0 AND 5 THEN 1
        ELSE 0
    END AS is_night,

    CASE
        WHEN t.txn_dow IN (0,6) THEN 1
        ELSE 0
    END AS is_weekend,

    COALESCE(ROUND(
        EXTRACT(EPOCH FROM (CAST(t.timestamp AS TIMESTAMP) - t.prev_ts)) / 60
    ,2), 0) AS time_gap_minutes,

    COALESCE(ROUND(t.amount - t.prev_amount,2), 0) AS amt_change,

    COALESCE(ROUND((t.amount - cp.avg_txn_amt) / NULLIF(s.std_amt,0),2), 0) AS amt_zscore,

    COALESCE(ROUND(t.amount / NULLIF(cp.max_txn_amount,0),2), 0) AS amt_pct_of_max,

    COALESCE(ROUND((t.balance_before - t.balance_after) / NULLIF(t.balance_before,0),2), 0) AS balance_drop_ratio,

    CASE
        WHEN t.amount > 2 * cp.avg_txn_amt THEN 1
        ELSE 0
    END AS high_amt_flag,

    t.txn_seq

FROM txn_base t

LEFT JOIN customer_profile cp
    ON t.account_id = cp.account_id

LEFT JOIN advanced_customer_profile ap
    ON t.account_id = ap.account_id

LEFT JOIN std_table s
    ON t.account_id = s.account_id
)

SELECT *,

    ROUND(amt_zscore * device_risk_flag, 2) AS zscore_x_device,

    ROUND(balance_drop_ratio * is_night, 2) AS drop_x_night,

    high_amt_flag * (1 - city_match) AS high_amt_x_new_city,

    ROUND(time_gap_minutes * amt_vs_avg, 2) AS gap_x_amount,

    ROUND(amt_vs_balance * device_risk_flag, 2) AS balance_x_device,

    balance_low_flag * high_amt_flag AS low_bal_x_high_amt,

    is_night * high_amt_flag AS night_x_high_amt,

    is_weekend * (1 - city_match) AS weekend_x_new_city,

    CASE
        WHEN time_gap_minutes < 30 AND balance_drop_ratio > 0.3
        THEN 1
        ELSE 0
    END AS rapid_drain,

    CASE
        WHEN amt_zscore > 2 AND city_match = 0
        THEN 1
        ELSE 0
    END AS sus_combo,

    device_risk_flag * is_night * balance_low_flag AS device_night_drain

FROM features
""")

print("fraud_model_input_final created")

print(
con.execute("""
SELECT * FROM fraud_model_input_final
LIMIT 10
""").fetchall()
)

cnt=con.execute("SELECT COUNT(*) FROM fraud_model_input_final").fetchone()[0]
print("total rows:",cnt)

cols=[r[0] for r in con.execute("DESCRIBE fraud_model_input_final").fetchall()]
print("columns:",len(cols))
print(cols)

con.close()
print("done")
