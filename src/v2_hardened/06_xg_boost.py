import pandas as pd
import duckdb 
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import classification_report,confusion_matrix,roc_auc_score

con=duckdb.connect("fraud_v2.duckdb")
df=con.execute("""select * from fraud_model_input""").df()
con.close()

print("shaped:",df.shape)
pos_count = df["is_fraud"].sum()
total_count = len(df)
print(f"Fraud ratio: {pos_count/total_count:.4f}  ({pos_count} / {total_count})")

cat_cols=["city","txn_type","channel","top_city","top_txn_type","device_id"]

encoders={}
for col in cat_cols:
    le=LabelEncoder()
    df[col]=le.fit_transform(df[col].astype(str))
    encoders[col]=le

x=df.drop(columns=["is_fraud","account_id"])
y=df["is_fraud"]

x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.20,random_state=45,stratify=y)

neg=(y_train==0).sum()
pos=(y_train==1).sum()
scale=neg/pos
print(f"scale_pos_weight: {scale:.2f}")

model=XGBClassifier(n_estimators=100,max_depth=6,scale_pos_weight=scale,learning_rate=0.1,eval_metric="logloss",random_state=45,tree_method="hist")
model.fit(x_train,y_train)

print("Model trained\n")
pred=model.predict(x_test)
prob=model.predict_proba(x_test)[:,1]

print("AUC Score:", roc_auc_score(y_test,prob))
print("Confusion Matrix:")
print(confusion_matrix(y_test,pred))
print("Classification Report:")
print(classification_report(y_test,pred))
