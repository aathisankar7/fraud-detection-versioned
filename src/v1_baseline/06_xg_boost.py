import pandas as pd
import duckdb 
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import classification_report,confusion_matrix,roc_auc_score
con=duckdb.connect("fraud.duckdb")
df=con.execute("""select * from fraud_model_input""").df()
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
neg=(y_train==0).sum()
pos=(y_train==1).sum()
scale=neg/pos
print("scale:",scale)
model=XGBClassifier(n_estimators=200,max_depth=6,scale_pos_weight=scale,learning_rate=0.10,subsample=0.80,colsample_bytree=0.80
,eval_metric="logloss",random_state=45)
model.fit(x_train,y_train)
print("model trained")
pred=model.predict(x_test)
prob=model.predict_proba(x_test)[:,1]
print("confusion matrix")
print(confusion_matrix(y_test,pred))
print("classification report")
print(classification_report(y_test,pred))
print("auc score:",roc_auc_score(y_test,prob))


