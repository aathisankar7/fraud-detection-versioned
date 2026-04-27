import duckdb
con=duckdb.connect("fraud.duckdb")
con.execute("""create or replace table customer_profile as 
select account_id,count(*) as tot_txn,
round(avg(amount),2) as avg_txn_amt,
round(max(amount),2)as max_txn_amount,
round(sum(amount),2)as total_spend,
count(distinct device_id) as distinct_devices
FROM 'data/transactions.csv'
GROUP BY account_id""")
print("customer_profile_created")
result=con.execute("""select * from customer_profile
limit 10""").fetchall()
print(result)
con.close()
print("done")

