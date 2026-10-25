"""
Step 3 - 测试集最终评估（只跑一次）+ 可解释性分析
运行: python src/evaluate.py      （需先运行 src/train.py）
产物: outputs/metrics/test_results.json, outputs/figures/*.png
"""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, average_precision_score,
                             confusion_matrix, f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score, roc_curve)

ROOT = Path(__file__).resolve().parent.parent
SPLIT = ROOT / "data" / "split"
MODEL_DIR = ROOT / "outputs" / "models"
FIG_DIR = ROOT / "outputs" / "figures"
METRIC_DIR = ROOT / "outputs" / "metrics"
FIG_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
TARGET = "obesity_binary"
MULTI_TARGET = "NObeyesdad"
POSITIVE_LABEL = "obesity(I-III)"

FS_LABEL = {"lifestyle": "Lifestyle-only", "measurement": "Measurement-inclusive"}
MODEL_LABEL = {"majority": "Majority baseline", "logreg": "Logistic Regression",
               "rf": "Random Forest"}


def evaluate_binary(bundle, X, y, tag):
    pipe = bundle["pipeline"]
    thr = bundle["threshold"]
    if "majority" in tag:
        proba = np.zeros(len(y), dtype=float)
    else:
        proba = pipe.predict_proba(X)[:, 1]
    pred = (proba >= thr).astype(int)
    return {
        "model": MODEL_LABEL[tag.split("__")[1]],
        "feature_set": FS_LABEL[tag.split("__")[0]],
        "threshold": thr,
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        f"precision_{POSITIVE_LABEL}": round(float(precision_score(y, pred, zero_division=0)), 4),
        f"recall_{POSITIVE_LABEL}": round(float(recall_score(y, pred, zero_division=0)), 4),
        f"f1_{POSITIVE_LABEL}": round(float(f1_score(y, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y, proba)), 4),
        "pr_auc": round(float(average_precision_score(y, proba)), 4),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }, proba, pred


def plot_curves(all_proba, y, save_path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for tag, proba in all_proba.items():
        if proba.max() == proba.min():
            continue
        fpr, tpr, _ = roc_curve(y, proba)
        axes[0].plot(fpr, tpr, lw=1.8,
                     label=f"{FS_LABEL[tag.split('__')[0]]} / {MODEL_LABEL[tag.split('__')[1]]}"
                           f"  (AUC={roc_auc_score(y, proba):.3f})")
        prec, rec, _ = precision_recall_curve(y, proba)
        axes[1].plot(rec, prec, lw=1.8,
                     label=f"{FS_LABEL[tag.split('__')[0]]} / {MODEL_LABEL[tag.split('__')[1]]}"
                           f"  (AP={average_precision_score(y, proba):.3f})")
    axes[0].plot([0, 1], [0, 1], "k--", lw=1, label="chance")
    axes[0].set_xlabel("False Positive Rate"); axes[0].set_ylabel("True Positive Rate")
    axes[0].set_title("ROC curves - test set"); axes[0].legend(fontsize=8); axes[0].grid(alpha=.3)
    axes[1].axhline(y.mean(), ls="--", c="k", lw=1, label=f"chance ({y.mean():.2f})")
    axes[1].set_xlabel("Recall"); axes[1].set_ylabel("Precision")
    axes[1].set_title("Precision-Recall curves - test set"); axes[1].legend(fontsize=8)
    axes[1].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close()


def plot_confusion(cm, title, save_path):
    cm = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["pred: non-obesity", "pred: obesity"])
    ax.set_yticklabels(["true: non-obesity", "true: obesity"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i][j]:,}", ha="center", va="center",
                    color="white" if cm[i][j] > cm.max() * 0.55 else "black", fontsize=13)
    ax.set_title(title); plt.colorbar(im, ax=ax, shrink=.8)
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close()


def plot_permutation(importances, feature_names, title, save_path, top=14):
    order = np.argsort(importances)[::-1][:top]
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.barh([PRETTY.get(feature_names[i], feature_names[i]) for i in order][::-1],
            importances[order][::-1], color="#4C72B0")
    ax.set_xlabel("Mean accuracy drop when feature is shuffled")
    ax.set_title(title); ax.grid(axis="x", alpha=.3)
    plt.tight_layout(); plt.savefig(save_path, dpi=150); plt.close()


PRETTY = {
    "Gender": "Gender", "Age": "Age",
    "family_history_with_overweight": "Family history of overweight",
    "FAVC": "Frequent high-calorie food", "FCVC": "Vegetable intake freq.",
    "NCP": "Meals per day", "CAEC": "Snacking between meals",
    "SMOKE": "Smoking", "CH2O": "Daily water intake",
    "SCC": "Calorie-intake monitoring", "FAF": "Physical activity freq.",
    "TUE": "Daily screen time", "CALC": "Alcohol consumption",
    "MTRANS": "Transport mode", "Height": "Height", "Weight": "Weight", "BMI": "BMI",
}


def main():
    test = pd.read_csv(SPLIT / "test.csv")
    y = test[TARGET].values
    out = {"n_test": int(len(test)), "test_obesity_rate": round(float(y.mean()), 4),
           "binary": [], "multiclass": []}
    all_proba = {}

    for fs in ["lifestyle", "measurement"]:
        for m in ["majority", "logreg", "rf"]:
            tag = f"{fs}__{m}"
            b = joblib.load(MODEL_DIR / f"{tag}.joblib")
            metrics, proba, pred = evaluate_binary(b, test[b["feature_cols"]], y, tag)
            out["binary"].append(metrics)
            all_proba[tag] = proba
            if m != "majority":
                plot_confusion(
                    metrics["confusion_matrix"],
                    f"{FS_LABEL[fs]} / {MODEL_LABEL[m]}\n"
                    f"F1={metrics[f'f1_{POSITIVE_LABEL}']:.3f}, "
                    f"Acc={metrics['accuracy']:.3f}",
                    FIG_DIR / f"cm_{fs}_{m}.png")

    plot_curves(all_proba, y, FIG_DIR / "roc_pr_curves.png")

    # ---------- 排列重要性（在测试集上做，衡量的是预测关联，不是因果）----------
    print("计算排列重要性 ...")
    perm_out = {}
    for fs in ["lifestyle", "measurement"]:
        b = joblib.load(MODEL_DIR / f"{fs}__rf.joblib")
        X = test[b["feature_cols"]]
        r = permutation_importance(b["pipeline"], X, y, n_repeats=10,
                                   random_state=SEED, n_jobs=-1, scoring="accuracy")
        imp = r.importances_mean
        perm_out[fs] = {c: round(float(v), 5)
                        for c, v in zip(b["feature_cols"], imp)}
        plot_permutation(imp, b["feature_cols"],
                         f"Permutation importance - {FS_LABEL[fs]} (Random Forest)",
                         FIG_DIR / f"perm_{fs}.png")
    out["permutation_importance"] = perm_out

    # ---------- 7 类多分类 ----------
    for fs in ["lifestyle", "measurement"]:
        b = joblib.load(MODEL_DIR / f"{fs}__multiclass.joblib")
        acc = float(b["pipeline"].score(test[b["feature_cols"]], test[MULTI_TARGET]))
        out["multiclass"].append({"feature_set": FS_LABEL[fs], "model": "Random Forest",
                                  "test_accuracy": round(acc, 4)})

    with open(METRIC_DIR / "test_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 78)
    print("测试集最终结果（二分类：肥胖 I-III vs 非肥胖）")
    print("=" * 78)
    df = pd.DataFrame(out["binary"])
    show = ["feature_set", "model", "accuracy", f"precision_{POSITIVE_LABEL}",
            f"recall_{POSITIVE_LABEL}", f"f1_{POSITIVE_LABEL}", "roc_auc", "pr_auc"]
    print(df[show].to_string(index=False))
    print("\n多分类（7 类，Random Forest）:")
    print(pd.DataFrame(out["multiclass"]).to_string(index=False))
    print(f"\n结果已保存 -> {METRIC_DIR / 'test_results.json'}")
    print(f"图表已保存 -> {FIG_DIR}")


if __name__ == "__main__":
    main()
