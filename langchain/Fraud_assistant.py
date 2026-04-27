import duckdb
import joblib
from langchain_ollama import ChatOllama

model = joblib.load("model/fraud_v4.pkl")
encoders = joblib.load("model/encoders.pkl")

account_id = input("Enter Account ID: ").strip()

con = duckdb.connect("fraud_v2.duckdb")

df = con.execute("""
select *
from fraud_model_input_final
where account_id = ?
limit 1
""", [account_id]).df()

con.close()

if df.empty:
    print("No account found")
    exit()

acc = df["account_id"][0]

X = df.drop(columns=["account_id", "is_fraud"]).copy()

cat_cols = [
    "city",
    "txn_type",
    "channel",
    "top_city",
    "top_txn_type",
    "device_id"
]

for col in cat_cols:
    X[col] = encoders[col].transform(X[col].astype(str))

score = model.predict_proba(X)[0][1]

if score >= 0.92:
    action = "BLOCK"
elif score >= 0.80:
    action = "REVIEW"
else:
    action = "ALLOW"

row = df.iloc[0].to_dict()

llm = ChatOllama(
    model="llama3.1:8b",
    temperature=0
)

prompt = f"""
You are a fraud analyst.

Account: {acc}
Fraud score: {score:.2f}
Suggested action: {action}

Transaction data:
{row}

Explain in simple words:

1. Why this looks risky or safe
2. Suspicious points
3. What to verify
4. Final recommendation
"""

response = llm.invoke(prompt)

print("\n" + "=" * 60)
print("Account ID :", acc)
print("Fraud Score:", round(score, 2))
print("Action     :", action)
print("=" * 60)
print(response.content)
print("=" * 60)