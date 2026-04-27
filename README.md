# Fraud Detection Project

so i built this fraud detection pipeline from scratch using duckdb and xgboost. I started with some basic fraud patterns just to get it working, then i made the data way more realistic to actually test it, and kept tuning the model until it was good.

it runs on 2M transactions and 50K customers across 4 versions.

## How it went

V1 got 99% accuracy because the fraud was too easy to spot. Then i made the fraud actually look like real life in V2 and my model completely broke. V3 and V4 are where i actually had to engineer my way out of it.

![version comparison](reports/version_comparison_chart.png)

## V1 - Baseline

Path: `src/v1_baseline`

This was just my first working pipeline.

Files i made:
1. `02_setup_duckdb.py` - sets up `fraud.duckdb`
2. `03_profile_duckdb.py` - creates `customer_profile`
3. `04_advanced_profiling.py` - creates `advanced_customer_profile`
4. `05_model_input.py` - creates `fraud_model_input`
5. `06_xg_boost.py` - runs the xgboost model

V1 fraud was just super obvious stuff:
- new city high amount
- midnight burst
- small rapid transactions
- new device drain

Output from terminal:
```text
shaped: (2000000, 18)
encoding completed
scale: 66.11127888930834
model trained
confusion matrix
[[393794    246]
 [     5   5955]]
classification report
              precision    recall  f1-score   support

           0       1.00      1.00      1.00    394040
           1       0.96      1.00      0.98      5960

    accuracy                           1.00    400000
   macro avg       0.98      1.00      0.99    400000
weighted avg       1.00      1.00      1.00    400000

auc score: 0.9999822240221584
```
it got 99.9% AUC which looks amazing but honestly any model could catch this. the fraud was too easy.

## V2 - Hardened Dataset

Path: `src/v2_hardened`

I used the same banking dataset but made the fraud realistic. This is where it actually got hard.

Files:
1. `02_setup_duckdb.py` - sets up `fraud_v2.duckdb`
2. `03_profile_duckdb.py` - creates `customer_profile`
3. `04_advanced_profiling.py` - creates `advanced_customer_profile`
4. `05_model_input.py` - creates `fraud_model_input`
5. `06_xg_boost.py` - runs model on the hardened data

V2 stealth fraud patterns i added:
- same city normal amount
- known device small drain
- daytime average amount
- weekend blend
- slow drain

Output:
```text
shaped: (2000000, 18)
Fraud ratio: 0.0149  (29732 / 2000000)
scale_pos_weight: 66.27
Model trained

AUC Score: 0.9559954387117546
Confusion Matrix:
[[320454  73600]
 [   454   5492]]
Classification Report:
              precision    recall  f1-score   support

           0       1.00      0.81      0.90    394054
           1       0.07      0.92      0.13      5946

    accuracy                           0.81    400000
   macro avg       0.53      0.87      0.51    400000
weighted avg       0.98      0.81      0.89    400000
```
Precision dropped to 8%. For every real fraud it caught, it flagged 12 innocent transactions. 62K false positives total. model completely broke here.

## V3 - Feature Upgrade

Path: `src/v3_feature_upgrade`

Uses the V2 hardened data but i upgraded the model input with some custom engineered features.

Files:
1. `01_model_input_v3.py` - creates `fraud_model_input_v3`
2. `02_xg_boost.py` - trains xgboost on the new features

Extra columns i added in V3:
- `balance_before`
- `balance_after`
- `amt_vs_avg`
- `amt_vs_median`
- `city_match`
- `amt_vs_balance`
- `device_risk_flag`
- `balance_low_flag`

Output (best threshold 0.90):
```text
shaped: (2000000, 26)
encoding completed
scale: 66.26645926175061
model trained
AUC Score: 0.9683045162011061
Threshold: 0.5
Confusion Matrix
[[342405  51649]
 [   541   5405]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.87      0.93    394054
           1       0.09      0.91      0.17      5946

    accuracy                           0.87    400000
   macro avg       0.55      0.89      0.55    400000
weighted avg       0.98      0.87      0.92    400000

Threshold: 0.6
Confusion Matrix
[[362670  31384]
 [  1013   4933]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.92      0.96    394054
           1       0.14      0.83      0.23      5946

    accuracy                           0.92    400000
   macro avg       0.57      0.87      0.60    400000
weighted avg       0.98      0.92      0.95    400000

Threshold: 0.7
Confusion Matrix
[[379919  14135]
 [  1508   4438]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.96      0.98    394054
           1       0.24      0.75      0.36      5946

    accuracy                           0.96    400000
   macro avg       0.62      0.86      0.67    400000
weighted avg       0.98      0.96      0.97    400000

Threshold: 0.8
Confusion Matrix
[[387332   6722]
 [  1870   4076]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.98      0.99    394054
           1       0.38      0.69      0.49      5946

    accuracy                           0.98    400000
   macro avg       0.69      0.83      0.74    400000
weighted avg       0.99      0.98      0.98    400000

Threshold: 0.9
Confusion Matrix
[[391624   2430]
 [  2318   3628]]
Classification Report
              precision    recall  f1-score   support

           0       0.99      0.99      0.99    394054
           1       0.60      0.61      0.60      5946

    accuracy                           0.99    400000
   macro avg       0.80      0.80      0.80    400000
weighted avg       0.99      0.99      0.99    400000
```
much better. False positives dropped from 62K down to 2.4K. F1 is 0.60 though, and it's missing 39% of the fraud.

## V4 - Final Improved Model

Path: `src/v4_improved`

This is my final version. i moved all feature engineering into SQL to keep things clean, and only kept the model script for training.

Files:
1. `01_model_input_final.py` - creates `fraud_model_input_final` (48 columns, everything in SQL now)
2. `02_final_model.py` - trains xgboost with oversampling

What i changed from V3:

New base features (all in SQL):
- `txn_hour`, `txn_dow` - time of transaction
- `is_night`, `is_weekend` - binary flags
- `time_gap_minutes` - gap from previous transaction
- `amt_change` - amount difference from previous txn
- `amt_zscore` - how unusual the amount is for that customer
- `amt_pct_of_max` - amount as % of customer's max
- `balance_drop_ratio` - how much balance dropped
- `high_amt_flag` - 1 if amount > 2x customer average
- `txn_seq` - transaction sequence number

Interaction features i made (in SQL):
- `zscore_x_device` - unusual amount on risky device
- `drop_x_night` - balance drain at night
- `high_amt_x_new_city` - high amount in unusual city
- `gap_x_amount` - rapid high amount transactions
- `balance_x_device` - big % of balance on risky device
- `low_bal_x_high_amt` - high amount when balance already low
- `night_x_high_amt` - high amount at night
- `weekend_x_new_city` - weekend txn in new city
- `rapid_drain` - fast txn + high balance drop
- `sus_combo` - high zscore + wrong city
- `device_night_drain` - risky device + night + low balance

Model changes:
- 4x fraud oversampling in training (1:66 ratio -> 1:13)
- 800 trees, depth 10, learning rate 0.03
- added regularization (alpha, lambda, gamma)

Output:
```text
shaped: (2000000, 48)
encoding completed
oversampled train shape: (1695144, 46)
fraud ratio now: 0.0702
scale: 13.25
model trained
AUC Score: 0.9876007582191277
best threshold: 0.92 best f1: 0.7013
Threshold: 0.5
Confusion Matrix
[[378496  15558]
 [   787   5159]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.96      0.98    394054
           1       0.25      0.87      0.39      5946

    accuracy                           0.96    400000
   macro avg       0.62      0.91      0.68    400000
weighted avg       0.99      0.96      0.97    400000

Threshold: 0.6
Confusion Matrix
[[382754  11300]
 [  1064   4882]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.97      0.98    394054
           1       0.30      0.82      0.44      5946

    accuracy                           0.97    400000
   macro avg       0.65      0.90      0.71    400000
weighted avg       0.99      0.97      0.98    400000

Threshold: 0.7
Confusion Matrix
[[387272   6782]
 [  1393   4553]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.98      0.99    394054
           1       0.40      0.77      0.53      5946

    accuracy                           0.98    400000
   macro avg       0.70      0.87      0.76    400000
weighted avg       0.99      0.98      0.98    400000

Threshold: 0.8
Confusion Matrix
[[391127   2927]
 [  1763   4183]]
Classification Report
              precision    recall  f1-score   support

           0       1.00      0.99      0.99    394054
           1       0.59      0.70      0.64      5946

    accuracy                           0.99    400000
   macro avg       0.79      0.85      0.82    400000
weighted avg       0.99      0.99      0.99    400000

Threshold: 0.9
Confusion Matrix
[[392830   1224]
 [  2096   3850]]
Classification Report
              precision    recall  f1-score   support

           0       0.99      1.00      1.00    394054
           1       0.76      0.65      0.70      5946

    accuracy                           0.99    400000
   macro avg       0.88      0.82      0.85    400000
weighted avg       0.99      0.99      0.99    400000

Threshold: 0.92
Confusion Matrix
[[393010   1044]
 [  2171   3775]]
Classification Report
              precision    recall  f1-score   support

           0       0.99      1.00      1.00    394054
           1       0.78      0.63      0.70      5946

    accuracy                           0.99    400000
   macro avg       0.89      0.82      0.85    400000
weighted avg       0.99      0.99      0.99    400000
```
Best result is at threshold 0.92: got 78% precision, 63% recall, and an F1 of 0.70. False positives are way down to 1,044 (compared to V2's 62,489). That's a 98% reduction!

## Langchain Fraud Assistant

Path: `Langchain/Fraud_assistant.py`

so after getting the V4 model working nicely, i realized a simple score isn't always enough to explain why a transaction is bad. i built an assistant using langchain and ollama to actually explain the decisions.

it uses a local llama3.1 8b model to look at the transaction data and act like a fraud analyst.

what it does:
- asks for an account ID
- pulls the transaction data from duckdb
- gets the prediction score from the V4 xgboost model
- sets an action (BLOCK >= 0.92, REVIEW >= 0.80, ALLOW otherwise)
- feeds all this into the llm to generate a plain english explanation

example output:
```text
Enter Account ID: ACC000060

============================================================
Account ID : ACC000060
Fraud Score: 0.0
Action     : ALLOW
============================================================
Here's the analysis:

**1. Why this looks safe:**
The account has a low fraud score of 0.00, and the suggested action is ALLOW. This indicates that the transaction appears normal and legitimate.

**2. Suspicious points:**
* The account has made 47 transactions in total, which is a relatively high number.
* The average transaction amount is $3937.93, which is significantly higher than the median transaction amount of $3795.57.

**3. What to verify:**
* Verify the user's identity and ensure that they are authorized to make large transactions.
* Confirm that the device used for this transaction (DEV1730) is registered with the bank.

**4. Final recommendation:**
Based on the analysis, I would recommend **ALLOWING** the transaction. While there are some suspicious points, they do not appear to be significant enough to warrant further investigation.
```
you can run it with:
`python3 Langchain/Fraud_assistant.py`

## Results Summary

```text
Version    AUC      Precision  Recall   F1      False Positives
V1         0.9999   96%        99%      0.98    246        (easy fraud, doesn't really count)
V2         0.9594   8%         90%      0.15    62,489     (realistic fraud, model broke)
V3         0.9683   60%        61%      0.60    2,430      (feature engineering helped)
V4         0.9876   78%        63%      0.70    1,044      (interactions + oversampling worked)
```

## Data

CSV files are in `data/`:
- `customers.csv` / `transactions.csv` - V1 data
- `customers_v2.csv` / `transactions_v2.csv` - V2 hardened data

duckdb files are local so i put them in .gitignore.

## Run It

From the repo root:

```bash
# v1
python3 src/v1_baseline/02_setup_duckdb.py
python3 src/v1_baseline/03_profile_duckdb.py
python3 src/v1_baseline/04_advanced_profiling.py
python3 src/v1_baseline/05_model_input.py
python3 src/v1_baseline/06_xg_boost.py

# v2
python3 src/v2_hardened/02_setup_duckdb.py
python3 src/v2_hardened/03_profile_duckdb.py
python3 src/v2_hardened/04_advanced_profiling.py
python3 src/v2_hardened/05_model_input.py
python3 src/v2_hardened/06_xg_boost.py

# v3 (needs v2 tables first)
python3 src/v3_feature_upgrade/01_model_input_v3.py
python3 src/v3_feature_upgrade/02_xg_boost.py

# v4 (needs v2 tables first)
python3 src/v4_improved/01_model_input_final.py
python3 src/v4_improved/02_final_model.py

# fraud assistant (needs v4 model and v2 tables)
python3 Langchain/Fraud_assistant.py
```
