import pandas as pd
import numpy as np
import duckdb 
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import classification_report,confusion_matrix,roc_auc_score,f1_score
import joblib
import os
con=duckdb.connect("fraud_v2.duckdb")
df=con.execute("""select * from fraud_model_input_final""").df()
con.close()
print("shaped:",df.shape)
cat_cols=["city","txn_type","channel","top_city","top_txn_type","device_id"]
encoders={}
for col in cat_cols:
    le=LabelEncoder()
    df[col]=le.fit_transform(df[col].astype(str))
    encoders[col]=le
print("encoding completed")
x=df.drop(columns=["is_fraud","account_id"])
y=df["is_fraud"]
x_train,x_test,y_train,y_test=train_test_split(x,y,test_size=0.20,random_state=45,stratify=y)
fraud_train=x_train[y_train==1]
fraud_labels=y_train[y_train==1]
copies=4
for i in range(copies):
    x_train=pd.concat([x_train,fraud_train])
    y_train=pd.concat([y_train,fraud_labels])
idx=np.random.RandomState(45).permutation(len(x_train))
x_train=x_train.iloc[idx].reset_index(drop=True)
y_train=y_train.iloc[idx].reset_index(drop=True)
print("oversampled train shape:",x_train.shape)
print("fraud ratio now:",round(y_train.mean(),4))
neg=(y_train==0).sum()
pos=(y_train==1).sum()
scale=neg/pos
print("scale:",round(scale,2))
model=XGBClassifier(n_estimators=800,max_depth=10,scale_pos_weight=scale,learning_rate=0.03
,subsample=0.85,colsample_bytree=0.85,min_child_weight=3,gamma=0.05
,reg_alpha=0.05,reg_lambda=1.5,eval_metric="logloss",random_state=45,tree_method="hist")
model.fit(x_train,y_train)
print("model trained")
os.makedirs("model", exist_ok=True)
joblib.dump(model, "model/fraud_v4.pkl")
joblib.dump(encoders, "model/encoders.pkl")
print("model saved")
prob = model.predict_proba(x_test)[:, 1]
print("AUC Score:", roc_auc_score(y_test, prob))
best_t=0.50
best_f1=0
for t in np.arange(0.30,0.96,0.01):
    p=(prob>=t).astype(int)
    f=f1_score(y_test,p)
    if f>best_f1:
        best_f1=f
        best_t=round(t,2)
print("best threshold:",best_t,"best f1:",round(best_f1,4))
thresholds=[0.50,0.60,0.70,0.80,0.90]
if best_t not in thresholds:
    thresholds.append(best_t)
    thresholds.sort()
for t in thresholds:
    pred = (prob >= t).astype(int)
    print("Threshold:", t)

    print("Confusion Matrix")
    print(confusion_matrix(y_test, pred))

    print("Classification Report")
    print(classification_report(y_test, pred))
