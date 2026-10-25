"""
Step 1 - 数据核查、清洗、标签定义与分层拆分
运行: python src/prepare_data.py
产物: data/clean.csv, data/split/{train,val,test}.csv, outputs/metrics/data_report.json
"""
import json
import time
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "obesity_level.csv"
OUT_DIR = ROOT / "data" / "split"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
ID_COL = "id"
RAW_TARGET = "0be1dad"          # 原始列名被混淆了（NObeyesdad -> 0be1dad）
TARGET_COL = "NObeyesdad"

# 标签拼写修复：数据集把首字母 N 写成了 0
LABEL_FIX = {"0rmal_Weight": "Normal_Weight"}

# 肥胖类 = I / II / III；其余（正常、超重 I/II、偏瘦）合并为非肥胖
OBESITY_CLASSES = {"Obesity_Type_I", "Obesity_Type_II", "Obesity_Type_III"}

# '0' 在这些列里代表 "no"（数据集把 no 写成了 0）
ZERO_AS_NO = ["CAEC", "CALC"]

NUMERIC_RAW = ["Age", "Height", "Weight", "FCVC", "NCP", "CH2O", "FAF", "TUE"]
CATEGORICAL = ["Gender", "family_history_with_overweight", "FAVC", "CAEC",
               "SMOKE", "SCC", "CALC", "MTRANS"]


def main():
    t0 = time.time()
    df = pd.read_csv(RAW)
    report = {"n_rows_raw": int(len(df)), "n_cols_raw": int(df.shape[1])}

    # ---------- 1. 列名与标签拼写修复 ----------
    rename_log = {}
    if RAW_TARGET in df.columns:
        df = df.rename(columns={RAW_TARGET: TARGET_COL})
        rename_log[RAW_TARGET] = TARGET_COL
    before = sorted(df[TARGET_COL].unique().tolist())
    df[TARGET_COL] = df[TARGET_COL].replace(LABEL_FIX)
    after = sorted(df[TARGET_COL].unique().tolist())
    report["column_renamed"] = rename_log
    report["labels_before_fix"] = before
    report["labels_after_fix"] = after

    # CAEC / CALC 里的 '0' 是 "no"，恢复成可读字符，避免被误当数值
    for c in ZERO_AS_NO:
        df[c] = df[c].replace({"0": "no", 0: "no"})

    # ---------- 2. 数据质量核查 ----------
    report["missing_per_col"] = {c: int(df[c].isna().sum()) for c in df.columns}
    report["n_missing_total"] = int(df.isna().sum().sum())
    feature_cols = [c for c in df.columns if c not in (ID_COL, TARGET_COL)]
    report["n_duplicate_rows_excl_id"] = int(df.duplicated(subset=feature_cols).sum())

    range_check = {}
    for c in NUMERIC_RAW:
        range_check[c] = {
            "min": float(df[c].min()), "max": float(df[c].max()),
            "mean": round(float(df[c].mean()), 4),
            "n_negative": int((df[c] < 0).sum()),
        }
    report["numeric_ranges"] = range_check
    report["categorical_levels"] = {c: sorted(df[c].astype(str).unique().tolist())
                                    for c in CATEGORICAL}

    # ---------- 3. 标签定义 ----------
    df["obesity_binary"] = df[TARGET_COL].isin(OBESITY_CLASSES).astype(int)
    dist = df[TARGET_COL].value_counts().to_dict()
    report["multiclass_distribution"] = {k: int(v) for k, v in dist.items()}
    report["binary_distribution"] = {
        "obesity(1)": int(df["obesity_binary"].sum()),
        "non_obesity(0)": int((1 - df["obesity_binary"]).sum()),
    }
    report["obesity_rate"] = round(float(df["obesity_binary"].mean()), 4)

    # ---------- 4. 衍生特征（BMI 只用于 measurement-inclusive 实验）----------
    df["BMI"] = df["Weight"] / (df["Height"] ** 2)
    report["bmi_by_class"] = {k: round(float(v), 2)
                              for k, v in df.groupby(TARGET_COL)["BMI"].mean().items()}

    # ---------- 5. 分层拆分 70 / 15 / 15 ----------
    strat = df[TARGET_COL]                      # 按 7 类分层，两类划分都保持原有等级比例
    train_df, rest_df = train_test_split(
        df, test_size=0.30, random_state=SEED, stratify=strat)
    val_df, test_df = train_test_split(
        rest_df, test_size=0.50, random_state=SEED, stratify=rest_df[TARGET_COL])

    report["split_sizes"] = {"train": int(len(train_df)), "val": int(len(val_df)),
                             "test": int(len(test_df))}
    report["split_obesity_rate"] = {
        "train": round(float(train_df["obesity_binary"].mean()), 4),
        "val": round(float(val_df["obesity_binary"].mean()), 4),
        "test": round(float(test_df["obesity_binary"].mean()), 4),
    }

    # ---------- 6. 落盘 ----------
    df.to_csv(ROOT / "data" / "clean.csv", index=False)
    for name, part in [("train", train_df), ("val", val_df), ("test", test_df)]:
        part.to_csv(OUT_DIR / f"{name}.csv", index=False)

    report["runtime_sec"] = round(time.time() - t0, 2)
    (ROOT / "outputs" / "metrics").mkdir(parents=True, exist_ok=True)
    with open(ROOT / "outputs" / "metrics" / "data_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
