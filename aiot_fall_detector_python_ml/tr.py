# train_rf.py
import os, json
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib

FEATURE_ORDER = ['amp10x', 'gvec', 'az', 'ax', 'ay', 'gz_spike', 'gx', 'gy', 'gz']

def load_data(data_dir='data'):
    falls, normals = [], []
    fall_dir, non_dir = Path(data_dir)/'fall', Path(data_dir)/'non_fall'

    if fall_dir.exists():
        for f in fall_dir.glob('*.csv'):
            df = pd.read_csv(f)
            df['label'] = 1
            falls.append(df)
    if non_dir.exists():
        for f in non_dir.glob('*.csv'):
            df = pd.read_csv(f)
            df['label'] = 0
            normals.append(df)

    if not falls and not normals:
        raise FileNotFoundError("No CSVs found under data/fall or data/non_fall")

    df = pd.concat([*falls, *normals], axis=0, ignore_index=True)
    return df

def engineer(df: pd.DataFrame):
    df = df.copy()
    # basic checks
    for col in ['ax','ay','az','gx','gy','gz']:
        if col not in df.columns:
            raise ValueError(f"Missing column {col}")

    df['amp10x'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2) * 10.0
    df['gvec']   = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2)
    df['gz_spike'] = df['gz'].diff().abs().fillna(0)
    X = df[FEATURE_ORDER]
    y = df['label'] if 'label' in df.columns else None
    return X, y

def main():
    out_dir = Path('backend/model'); out_dir.mkdir(parents=True, exist_ok=True)
    print("Loading data...")
    df = load_data('data')
    print(df['label'].value_counts())

    print("Engineering features...")
    X, y = engineer(df)

    # scale features (helps when deployment data distribution shifts)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    Xtr, Xte, ytr, yte = train_test_split(Xs, y, test_size=0.2, random_state=42, stratify=y)

    print("Training RandomForest...")
    clf = RandomForestClassifier(
        n_estimators=200, max_depth=14, class_weight='balanced', n_jobs=-1, random_state=42
    )
    clf.fit(Xtr, ytr)

    yp = clf.predict(Xte)
    print("\nAccuracy:", accuracy_score(yte, yp))
    print(classification_report(yte, yp, digits=4))

    # save artifacts
    joblib.dump(clf, out_dir/'trained_model.pkl')
    joblib.dump(scaler, out_dir/'scaler.pkl')
    with open(out_dir/'feature_order.json','w') as f:
        json.dump(FEATURE_ORDER, f)

    print("\nSaved to", out_dir)

if __name__ == "__main__":
    main()
