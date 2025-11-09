import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
from pathlib import Path

def load_data(data_dir):
    """Load and preprocess the dataset"""
    # Load fall and non-fall data
    fall_data = []
    non_fall_data = []
    
    # Load fall data (assuming CSV files with appropriate columns)
    fall_dir = os.path.join(data_dir, 'fall')
    if os.path.exists(fall_dir):
        for file in os.listdir(fall_dir):
            if file.endswith('.csv'):
                df = pd.read_csv(os.path.join(fall_dir, file))
                fall_data.append(df)
    
    # Load non-fall data
    non_fall_dir = os.path.join(data_dir, 'non_fall')
    if os.path.exists(non_fall_dir):
        for file in os.listdir(non_fall_dir):
            if file.endswith('.csv'):
                df = pd.read_csv(os.path.join(non_fall_dir, file))
                non_fall_data.append(df)
    
    # Combine data and create labels
    if fall_data:
        fall_df = pd.concat(fall_data, axis=0)
        fall_df['label'] = 1  # 1 for fall
    
    if non_fall_data:
        non_fall_df = pd.concat(non_fall_data, axis=0)
        non_fall_df['label'] = 0  # 0 for non-fall
    
    # Combine all data
    if fall_data and non_fall_data:
        all_data = pd.concat([fall_df, non_fall_df], axis=0)
    elif fall_data:
        all_data = fall_df
    elif non_fall_data:
        all_data = non_fall_df
    else:
        raise FileNotFoundError("No data found in the specified directories")
    
    return all_data

def extract_features(df):
    """Extract features from raw sensor data"""
    features = []
    
    # Required features based on the existing model
    df['amp10x'] = np.sqrt(df['ax']**2 + df['ay']**2 + df['az']**2) * 10.0
    df['gvec'] = np.sqrt(df['gx']**2 + df['gy']**2 + df['gz']**2)
    df['gz_spike'] = df['gz'].diff().abs().fillna(0)
    
    # Select features in the correct order
    feature_cols = ['amp10x', 'gvec', 'az', 'ax', 'ay', 'gz_spike', 'gx', 'gy', 'gz']
    
    return df[feature_cols], df['label'] if 'label' in df.columns else None

def train_model(X, y):
    """Train a Random Forest classifier"""
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Initialize and train the model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced',
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Evaluate the model
    print("\nModel Evaluation:")
    print("-" * 50)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    return model, X_test, y_test

def save_model(model, output_dir):
    """Save the trained model and feature order"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save the model
    model_path = os.path.join(output_dir, 'trained_model.pkl')
    joblib.dump(model, model_path)
    
    # Save feature order
    feature_order = ['amp10x', 'gvec', 'az', 'ax', 'ay', 'gz_spike', 'gx', 'gy', 'gz']
    with open(os.path.join(output_dir, 'feature_order.json'), 'w') as f:
        json.dump(feature_order, f)
    
    print(f"\nModel and feature order saved to {output_dir}")

def main():
    # Configuration
    DATA_DIR = 'data'  # Directory containing 'fall' and 'non_fall' subdirectories with CSV files
    OUTPUT_DIR = 'backend/model'  # Where to save the trained model
    
    print("Loading and preprocessing data...")
    try:
        data = load_data(DATA_DIR)
        print(f"\nLoaded {len(data)} samples")
        print(f"Class distribution:\n{data['label'].value_counts()}")
        
        print("\nExtracting features...")
        X, y = extract_features(data)
        
        print("\nTraining model...")
        model, X_test, y_test = train_model(X, y)
        
        # Save the trained model
        save_model(model, OUTPUT_DIR)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nPlease make sure you have the following directory structure:")
        print("data/")
        print("├── fall/")
        print("│   ├── fall_data1.csv")
        print("│   └── fall_data2.csv")
        print("└── non_fall/")
        print("    ├── normal_activity1.csv")
        print("    └── normal_activity2.csv")
        print("\nCSV files should contain columns: ax, ay, az, gx, gy, gz")

if __name__ == "__main__":
    main()
