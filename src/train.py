"""
Step 2 - 在训练集上拟合模型，用验证集选超参与判定阈值
运行: python src/train.py
产物: outputs/models/*.joblib, outputs/metrics/val_results.json

原则：验证集只用于选超参和阈值；测试集在本脚本中完全不读取。
"""
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score, average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
SPLIT = ROOT / "data" / "split"
MODEL_DIR = ROOT / "outputs" / "models"
METRIC_DIR = ROOT / "outputs" / "metrics"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
METRIC_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
TARGET = "obesity_binary"
MULTI_TARGET = "NObeyesdad"

# 两套特征集：A 只用生活方式，B 额外加入身高/体重/BMI
LIFESTYLE = ["Gender", "Age", "family_history_with_overweight", "FAVC", "FCVC",
             "NCP", "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE", "CALC", "MTRANS"]
FEATURE_SETS = {
    "lifestyle": LIFESTYLE,
    "measurement": LIFESTYLE + ["Height", "Weight", "BMI"],
}
NUMERIC = ["Age", "FCVC", "NCP", "CH2O", "FAF", "TUE", "Height", "Weight", "BMI"]


def make_preprocessor(cols):
    """预处理只在训练数据上 fit，通过 Pipeline 保证不泄漏验证/测试集统计量。"""
    num = [c for c in cols if c in NUMERIC]
    cat = [c for c in cols if c not in NUMERIC]
    return ColumnTransformer([
        ("num", Pipeline([("impute", "passthrough"), ("scale", StandardScaler())]), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ])


def grid_for(model_name):
    if model_name == "logreg":
        return [{"C": c, "class_weight": w}
                for c in (0.1, 1.0, 10.0) for w in (None, "balanced")]
    if model_name == "rf":
        return [{"n_estimators": 400, "max_depth": d, "min_samples_leaf": l,
                 "class_weight": w}
                for d in (None, 16) for l in (1, 3) for w in (None, "balanced")]
    return [{}]


def build_model(model_name, params):
    if model_name == "majority":
        return DummyClassifier(strategy="most_frequent")
    if model_name == "logreg":
        return LogisticRegression(max_iter=2000, random_state=SEED, **params)
    if model_name == "rf":
        return RandomForestClassifier(random_state=SEED, n_jobs=-1, **params)
    raise ValueError(model_name)


def pick_threshold(y_true, proba):
    """在验证集上扫描阈值，取 obesity 类 F1 最高的那个。"""
    best_t, best_f1 = 0.5, -1.0
    for t in np.linspace(0.05, 0.95, 91):
        f1 = f1_score(y_true, (proba >= t).astype(int), zero_division=0)
        if f1 > best_f1:
            best_f1, best_t = f1, float(t)
    return best_t, best_f1


def main():
    train = pd.read_csv(SPLIT / "train.csv")
    val = pd.read_csv(SPLIT / "val.csv")
    results = {"seed": SEED, "n_train": int(len(train)), "n_val": int(len(val)), "runs": []}
    bundle = {}

    for fs_name, cols in FEATURE_SETS.items():
        for model_name in ["majority", "logreg", "rf"]:
            Xtr, ytr = train[cols], train[TARGET].values
            Xva, yva = val[cols], val[TARGET].values

            best = None
            for params in grid_for(model_name):
                pipe = Pipeline([("prep", make_preprocessor(cols)),
                                 ("clf", build_model(model_name, params))])
                t0 = time.time()
                pipe.fit(Xtr, ytr)
                fit_sec = time.time() - t0

                if model_name == "majority":
                    proba = np.zeros(len(yva), dtype=float)
                else:
                    proba = pipe.predict_proba(Xva)[:, 1]
                auc = (0.5 if model_name == "majority"
                       else float(roc_auc_score(yva, proba)))
                ap = (float(yva.mean()) if model_name == "majority"
                      else float(average_precision_score(yva, proba)))
                thr, thr_f1 = pick_threshold(yva, proba)

                rec = {"feature_set": fs_name, "model": model_name, "params": params,
                       "fit_sec": round(fit_sec, 3), "val_roc_auc": round(auc, 4),
                       "val_pr_auc": round(ap, 4), "threshold": round(thr, 3),
                       "val_f1_at_threshold": round(thr_f1, 4)}
                results["runs"].append(rec)
                if best is None or rec["val_f1_at_threshold"] > best[0]["val_f1_at_threshold"]:
                    best = (rec, pipe, proba)
                print(f"[{fs_name:11s}][{model_name:8s}] "
                      f"AUC={rec['val_roc_auc']:.4f} PR-AUC={rec['val_pr_auc']:.4f} "
                      f"F1@{rec['threshold']:.2f}={rec['val_f1_at_threshold']:.4f} "
                      f"params={params}")

            rec, pipe, _ = best
            bundle[f"{fs_name}__{model_name}"] = {
                "pipeline": pipe, "feature_cols": cols,
                "threshold": rec["threshold"], "val_metrics": rec}
            joblib.dump(bundle[f"{fs_name}__{model_name}"],
                        MODEL_DIR / f"{fs_name}__{model_name}.joblib", compress=3)
            print(f"  -> 选定 {fs_name}/{model_name}: {rec['params']}\n")

    # ---------- 扩展实验：7 类多分类 ----------
    print("=== 可选扩展：7 类多分类 ===")
    multi = {}
    for fs_name, cols in FEATURE_SETS.items():
        pipe = Pipeline([("prep", make_preprocessor(cols)),
                         ("clf", RandomForestClassifier(
                             n_estimators=400, random_state=SEED, n_jobs=-1))])
        t0 = time.time()
        pipe.fit(train[cols], train[MULTI_TARGET])
        fit_sec = time.time() - t0
        acc = float(pipe.score(val[cols], val[MULTI_TARGET]))
        results.setdefault("multiclass", []).append(
            {"feature_set": fs_name, "model": "rf", "val_accuracy": round(acc, 4),
             "fit_sec": round(fit_sec, 2)})
        print(f"[{fs_name:11s}] 7-class val accuracy = {acc:.4f}  ({fit_sec:.1f}s)")
        multi[f"{fs_name}__multiclass"] = {"pipeline": pipe, "feature_cols": cols}
        joblib.dump(multi[f"{fs_name}__multiclass"],
                    MODEL_DIR / f"{fs_name}__multiclass.joblib", compress=3)

    results["multiclass"] = results.get("multiclass", [])
    with open(METRIC_DIR / "val_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n验证集结果已保存 -> {METRIC_DIR / 'val_results.json'}")


if __name__ == "__main__":
    main()
