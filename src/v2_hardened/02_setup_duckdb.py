import duckdb
con=duckdb.connect("fraud_v2.duckdb")
print("connected")
result=con.execute("select 1 as status").fetchall()
print(result)
con.close()
print("successfully created")