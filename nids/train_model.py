"""
Model Training Script for NIDS
University of Nigeria, Nsukka - Department of Computer Science
Trains Random Forest Pipeline on NSL-KDD dataset and computes evaluation metrics.
"""

import os
import sys
import json
import joblib
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from preprocessing import (
    COLUMN_NAMES, FEATURE_COLUMNS, CATEGORICAL_FEATURES,
    encode_label
)
from database import init_db, insert_model_info

def train_and_evaluate():
    print("=" * 70)
    print("UNN Department of Computer Science - NIDS Model Training")
    print("=" * 70)

    # Initialize database
    init_db()

    data_dir = BASE_DIR / "data"
    model_dir = BASE_DIR / "model"
    model_dir.mkdir(exist_ok=True, parents=True)

    train_path = data_dir / "KDDTrain+.txt"
    test_path = data_dir / "KDDTest+.txt"

    if not train_path.exists() or not test_path.exists():
        print(f"Error: Dataset files not found in {data_dir}")
        print("Please ensure KDDTrain+.txt and KDDTest+.txt are located in nids/data/")
        sys.exit(1)

    print(f"Loading training data from {train_path}...")
    train_df = pd.read_csv(train_path, names=COLUMN_NAMES, header=None)
    print(f"Training records loaded: {len(train_df)}")

    print(f"Loading test data from {test_path}...")
    test_df = pd.read_csv(test_path, names=COLUMN_NAMES, header=None)
    print(f"Testing records loaded: {len(test_df)}")

    # Prepare features and targets
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df['label'].apply(encode_label)

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df['label'].apply(encode_label)

    print(f"Training target distribution: Normal={sum(y_train==0)}, Attack={sum(y_train==1)}")
    print(f"Testing target distribution: Normal={sum(y_test==0)}, Attack={sum(y_test==1)}")

    # Build Pipeline
    print("\nConstructing Machine Learning Pipeline...")
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), CATEGORICAL_FEATURES)
        ],
        remainder='passthrough'
    )

    rf_classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', rf_classifier)
    ])

    print("Fitting Random Forest Pipeline on KDDTrain+...")
    start_time = datetime.now()
    pipeline.fit(X_train, y_train)
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"Training completed in {elapsed:.2f} seconds.")

    # Evaluate on KDDTest+
    print("\nEvaluating model on KDDTest+ benchmark...")
    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "false_positive_rate": round(float(fpr), 4),
        "confusion_matrix": [
            [int(tn), int(fp)],
            [int(fn), int(tp)]
        ],
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "total_test_samples": len(y_test)
    }

    print("-" * 50)
    print(f"Accuracy:              {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
    print(f"Precision:             {metrics['precision']:.4f}")
    print(f"Recall:                {metrics['recall']:.4f}")
    print(f"F1 Score:              {metrics['f1_score']:.4f}")
    print(f"False Positive Rate:   {metrics['false_positive_rate']:.4f}")
    print(f"Confusion Matrix:      TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print("-" * 50)

    # Save metrics to model/metrics.json
    metrics_path = model_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
    print(f"Metrics saved to {metrics_path}")

    # Top 15 Feature Importances
    fitted_preprocessor = pipeline.named_steps['preprocessor']
    feature_names = [f.replace('cat__', '').replace('remainder__', '') for f in fitted_preprocessor.get_feature_names_out()]
    importances = pipeline.named_steps['classifier'].feature_importances_

    feature_imp_list = sorted(
        [{"feature": name, "importance": round(float(imp), 5)} for name, imp in zip(feature_names, importances)],
        key=lambda x: x["importance"],
        reverse=True
    )
    top_15_features = feature_imp_list[:15]

    feat_path = model_dir / "feature_importance.json"
    with open(feat_path, "w", encoding="utf-8") as f:
        json.dump(top_15_features, f, indent=4)
    print(f"Top 15 Feature Importances saved to {feat_path}")

    # Save compressed pipeline model
    model_save_path = model_dir / "rf_model.joblib"
    joblib.dump(pipeline, model_save_path, compress=3)
    file_size_mb = os.path.getsize(model_save_path) / (1024 * 1024)
    print(f"Trained model saved to {model_save_path} ({file_size_mb:.2f} MB)")

    # Record model info into database
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_model_info(
        model_name="Random Forest Classifier (100 Trees)",
        dataset="NSL-KDD (KDDTrain+ / KDDTest+)",
        date_trained=date_str,
        accuracy=round(float(acc), 4)
    )
    print("Model details registered in ModelInformation database table.")

    # Generate data/traffic_log.csv (~500 rows from KDDTest+, mix of normal and attack, no label column)
    print("\nGenerating simulation datasets...")
    test_normal = test_df[test_df['label'].apply(encode_label) == 0]
    test_attack = test_df[test_df['label'].apply(encode_label) == 1]

    # Sample 250 normal and 250 attack
    n_sample_norm = min(250, len(test_normal))
    n_sample_att = min(250, len(test_attack))
    sample_500 = pd.concat([
        test_normal.sample(n=n_sample_norm, random_state=42),
        test_attack.sample(n=n_sample_att, random_state=42)
    ]).sample(frac=1.0, random_state=42) # shuffle

    traffic_log_df = sample_500[FEATURE_COLUMNS]
    traffic_log_path = data_dir / "traffic_log.csv"
    traffic_log_df.to_csv(traffic_log_path, index=False)
    print(f"Traffic monitoring log generated: {traffic_log_path} ({len(traffic_log_df)} records)")

    # Generate data/sample_upload.csv (20 rows, mix of normal and attack, no label column)
    sample_20 = pd.concat([
        test_normal.sample(n=10, random_state=101),
        test_attack.sample(n=10, random_state=101)
    ]).sample(frac=1.0, random_state=101)

    sample_upload_df = sample_20[FEATURE_COLUMNS]
    sample_upload_path = data_dir / "sample_upload.csv"
    sample_upload_df.to_csv(sample_upload_path, index=False)
    print(f"Sample CSV for upload testing generated: {sample_upload_path} ({len(sample_upload_df)} records)")

    print("\n" + "=" * 70)
    print("NIDS Model Training and Dataset Preparation Complete!")
    print("=" * 70)

if __name__ == "__main__":
    train_and_evaluate()
