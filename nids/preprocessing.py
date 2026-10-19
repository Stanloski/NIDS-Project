"""
Data Preprocessing and Schema Definitions for NIDS
University of Nigeria, Nsukka - Department of Computer Science
NSL-KDD Dataset Feature Definitions and Utilities
"""

import pandas as pd
import numpy as np

# 43 Columns of NSL-KDD (41 features + label + difficulty_level)
COLUMN_NAMES = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'label', 'difficulty_level'
]

# The 41 features passed to the Machine Learning Model
FEATURE_COLUMNS = COLUMN_NAMES[:41]

# Categorical features requiring encoding
CATEGORICAL_FEATURES = ['protocol_type', 'service', 'flag']

# Numeric features
NUMERIC_FEATURES = [col for col in FEATURE_COLUMNS if col not in CATEGORICAL_FEATURES]

# Feature groups for structured presentation in the manual prediction form
FEATURE_GROUPS = [
    {
        "group_id": "basic",
        "title": "Basic Connection Features",
        "description": "Fundamental network protocol, port service, and byte exchange attributes",
        "fields": [
            {"name": "duration", "label": "Duration (seconds)", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "protocol_type", "label": "Protocol Type", "type": "select", "options": ["tcp", "udp", "icmp"], "default": "tcp"},
            {"name": "service", "label": "Service", "type": "text", "default": "http", "placeholder": "e.g. http, private, smtp, ftp_data"},
            {"name": "flag", "label": "Status Flag", "type": "text", "default": "SF", "placeholder": "e.g. SF, S0, REJ, RSTR"},
            {"name": "src_bytes", "label": "Source Bytes", "type": "number", "default": 181, "min": 0, "step": 1},
            {"name": "dst_bytes", "label": "Destination Bytes", "type": "number", "default": 5450, "min": 0, "step": 1},
            {"name": "land", "label": "Land (1=Same host/port, 0=No)", "type": "select", "options": [0, 1], "default": 0},
            {"name": "wrong_fragment", "label": "Wrong Fragments", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "urgent", "label": "Urgent Packets", "type": "number", "default": 0, "min": 0, "step": 1}
        ]
    },
    {
        "group_id": "content",
        "title": "Content & Payload Features",
        "description": "Internal connection behavior, elevated access indicators, and shell activity",
        "fields": [
            {"name": "hot", "label": "Hot Indicators", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "num_failed_logins", "label": "Failed Logins", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "logged_in", "label": "Logged In (1=Yes, 0=No)", "type": "select", "options": [0, 1], "default": 1},
            {"name": "num_compromised", "label": "Compromised Conditions", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "root_shell", "label": "Root Shell Obtained", "type": "select", "options": [0, 1], "default": 0},
            {"name": "su_attempted", "label": "su Root Attempted", "type": "select", "options": [0, 1], "default": 0},
            {"name": "num_root", "label": "Root Operations", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "num_file_creations", "label": "File Creations", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "num_shells", "label": "Shell Prompts", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "num_access_files", "label": "Access Control Files", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "num_outbound_cmds", "label": "Outbound Commands", "type": "number", "default": 0, "min": 0, "step": 1},
            {"name": "is_host_login", "label": "Host Login", "type": "select", "options": [0, 1], "default": 0},
            {"name": "is_guest_login", "label": "Guest Login", "type": "select", "options": [0, 1], "default": 0}
        ]
    },
    {
        "group_id": "traffic",
        "title": "Time-based Traffic Features",
        "description": "Connection statistics within a 2-second temporal observation window",
        "fields": [
            {"name": "count", "label": "Past 2s Connection Count", "type": "number", "default": 8, "min": 0, "step": 1},
            {"name": "srv_count", "label": "Past 2s Service Count", "type": "number", "default": 8, "min": 0, "step": 1},
            {"name": "serror_rate", "label": "SYN Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "srv_serror_rate", "label": "Service SYN Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "rerror_rate", "label": "REJ Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "srv_rerror_rate", "label": "Service REJ Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "same_srv_rate", "label": "Same Service Rate", "type": "number", "default": 1.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "diff_srv_rate", "label": "Diff Service Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "srv_diff_host_rate", "label": "Service Diff Host Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01}
        ]
    },
    {
        "group_id": "host",
        "title": "Host-based Traffic Features",
        "description": "Cumulative destination host network statistics over the past 100 connections",
        "fields": [
            {"name": "dst_host_count", "label": "Dst Host Count", "type": "number", "default": 9, "min": 0, "step": 1},
            {"name": "dst_host_srv_count", "label": "Dst Host Srv Count", "type": "number", "default": 9, "min": 0, "step": 1},
            {"name": "dst_host_same_srv_rate", "label": "Dst Host Same Srv Rate", "type": "number", "default": 1.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_diff_srv_rate", "label": "Dst Host Diff Srv Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_same_src_port_rate", "label": "Dst Host Same Port Rate", "type": "number", "default": 0.11, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_srv_diff_host_rate", "label": "Dst Host Srv Diff Host Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_serror_rate", "label": "Dst Host SYN Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_srv_serror_rate", "label": "Dst Host Srv SYN Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_rerror_rate", "label": "Dst Host REJ Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01},
            {"name": "dst_host_srv_rerror_rate", "label": "Dst Host Srv REJ Error Rate", "type": "number", "default": 0.0, "min": 0, "max": 1, "step": 0.01}
        ]
    }
]

def encode_label(label_value):
    """
    Transforms raw NSL-KDD attack labels to binary classification:
    'normal' -> 0 (Normal)
    anything else -> 1 (Attack)
    """
    cleaned = str(label_value).strip().lower()
    return 0 if cleaned == 'normal' else 1

def validate_and_prepare_record(record_dict):
    """
    Validates that all 41 feature columns are present and correctly formatted.
    Raises ValueError with specific details if any column is missing or invalid.
    Returns a cleaned single-row pandas DataFrame matching FEATURE_COLUMNS order.
    """
    missing = [col for col in FEATURE_COLUMNS if col not in record_dict or record_dict[col] is None or str(record_dict[col]).strip() == ""]
    if missing:
        raise ValueError(f"Missing required feature columns: {', '.join(missing[:5])}" + (f" and {len(missing)-5} more" if len(missing) > 5 else ""))

    cleaned = {}
    for col in FEATURE_COLUMNS:
        val = record_dict[col]
        if col in CATEGORICAL_FEATURES:
            cleaned[col] = str(val).strip()
        else:
            try:
                # Convert numeric values
                cleaned[col] = float(val)
            except (ValueError, TypeError):
                raise ValueError(f"Feature '{col}' must be a valid numeric value, received: '{val}'")

    return pd.DataFrame([cleaned], columns=FEATURE_COLUMNS)
