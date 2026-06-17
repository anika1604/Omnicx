"""
Train XGBoost churn predictor on real Telco Customer Churn dataset.
"""
import os
import sys
import pickle
import urllib.request
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

DATA_URL    = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
DATA_PATH   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'telco_churn.csv'))
OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'ml', 'churn', 'model.pkl'))

os.makedirs(os.path.dirname(DATA_PATH),   exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


def download_data():
    if not os.path.exists(DATA_PATH):
        print("Downloading Telco Churn dataset...")
        urllib.request.urlretrieve(DATA_URL, DATA_PATH)
        print(f"Saved to {DATA_PATH}")
    else:
        print("Dataset already downloaded")


def prepare_features(df: pd.DataFrame):
    df = df.copy()

    # Fix TotalCharges
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"].fillna(df["TotalCharges"].median(), inplace=True)

    # Binary columns
    binary_cols = ["Partner", "Dependents", "PhoneService", "PaperlessBilling"]
    for col in binary_cols:
        df[col] = (df[col] == "Yes").astype(int)

    # Encode categoricals
    cat_cols = [
        "gender", "MultipleLines", "InternetService",
        "OnlineSecurity", "OnlineBackup", "DeviceProtection",
        "TechSupport", "StreamingTV", "StreamingMovies",
        "Contract", "PaymentMethod",
    ]
    le = LabelEncoder()
    for col in cat_cols:
        df[col] = le.fit_transform(df[col].astype(str))

    # Target
    df["Churn"] = (df["Churn"] == "Yes").astype(int)

    FEATURES = [
        "tenure", "MonthlyCharges", "TotalCharges",
        "Contract", "InternetService", "PaymentMethod",
        "Partner", "Dependents", "PhoneService", "PaperlessBilling",
        "MultipleLines", "OnlineSecurity", "OnlineBackup",
        "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
        "gender", "SeniorCitizen",
    ]

    return df[FEATURES], df["Churn"], FEATURES


def train():
    download_data()

    print("Loading dataset...")
    df = pd.read_csv(DATA_PATH)
    print(f"Shape: {df.shape}, Churn rate: {(df['Churn']=='Yes').mean():.1%}")

    X, y, features = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training XGBoost model...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # Evaluate
    y_pred  = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    auc     = roc_auc_score(y_test, y_proba)

    print(f"\nModel Performance:")
    print(f"  AUC-ROC: {auc:.3f}")
    print(classification_report(y_test, y_pred, target_names=["Retained", "Churned"]))

    print("Feature Importance (top 10):")
    for feat, imp in sorted(
        zip(features, model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )[:10]:
        bar = "█" * int(imp * 100)
        print(f"  {feat:25} {bar} {imp:.3f}")

    # Save
    payload = {"model": model, "features": features}
    with open(OUTPUT_PATH, "wb") as f:
        pickle.dump(payload, f)
    print(f"\n✅ Churn model saved to {OUTPUT_PATH}")
    print(f"   AUC-ROC: {auc:.3f} (industry benchmark: >0.80)")


if __name__ == "__main__":
    train()