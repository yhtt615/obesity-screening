"""
第三次报告的新增分析：交叉验证稳健性、公平性、概率校准
运行: python src/robustness.py
产物: outputs/metrics/robustness.json + outputs/figures/{cv,fairness,calibration}.png

规范：交叉验证只用 train+val；校准器只用 validation 拟合；测试集只用于最终评估。
"""
import json
import time
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, f1_score,
                             roc_auc_score, confusion_matrix)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
SPLIT = ROOT / "data" / "split"
FIG = ROOT / "outputs" / "figures"
MET = ROOT / "outputs" / "metrics"
FIG.mkdir(parents=True, exist_ok=True)
SEED = 42
TARGET = "obesity_binary"

LIFESTYLE = ["Gender", "Age", "family_history_with_overweight", "FAVC", "FCVC",
             "NCP", "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE", "CALC", "MTRANS"]
FEATURE_SETS = {"lifestyle": LIFESTYLE, "measurement": LIFESTYLE + ["Height", "Weight", "BMI"]}
NUMERIC = ["Age", "FCVC", "NCP", "CH2O", "FAF", "TUE", "Height", "Weight", "BMI"]


def make_pipe(model, cols):
    num = [c for c in cols if c in NUMERIC]
    cat = [c for c in cols if c not in NUMERIC]
    prep = ColumnTransformer([
        ("num", StandardScaler(), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat)])
    if model == "lr":
        clf = LogisticRegression(max_iter=2000, random_state=SEED)
    else:
        clf = RandomForestClassifier(n_estimators=400, max_depth=16, min_samples_leaf=3,
                                     class_weight="balanced", random_state=SEED, n_jobs=-1)
    return Pipeline([("prep", prep), ("clf", clf)])


def cross_validate(trainval):
    """5 折分层交叉验证，报告 mean ± std，证明单次拆分不是侥幸。"""
    out = []
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for fs, cols in FEATURE_SETS.items():
        X = trainval[cols]
        y = trainval[TARGET].values
        for model in ["lr", "rf"]:
            f1s, aucs, accs = [], [], []
            for tr, va in skf.split(X, y):
                pipe = make_pipe(model, cols)
                pipe.fit(X.iloc[tr], y[tr])
                proba = pipe.predict_proba(X.iloc[va])[:, 1]
                pred = (proba >= 0.5).astype(int)
                f1s.append(f1_score(y[va], pred))
                aucs.append(roc_auc_score(y[va], proba))
                accs.append(accuracy_score(y[va], pred))
            rec = {"feature_set": fs, "model": model.upper(),
                   "cv_f1_mean": round(float(np.mean(f1s)), 4),
                   "cv_f1_std": round(float(np.std(f1s)), 4),
                   "cv_auc_mean": round(float(np.mean(aucs)), 4),
                   "cv_auc_std": round(float(np.std(aucs)), 4),
                   "cv_acc_mean": round(float(np.mean(accs)), 4),
                   "cv_acc_std": round(float(np.std(accs)), 4)}
            out.append(rec)
            print(f"[CV] {fs:11s} {model.upper():3s}  F1={rec['cv_f1_mean']:.4f}±{rec['cv_f1_std']:.4f}  "
                  f"AUC={rec['cv_auc_mean']:.4f}±{rec['cv_auc_std']:.4f}")
    return out


def fairness(test):
    """按性别和年龄组检查错误率是否均衡。"""
    out = []
    for fs in ["lifestyle", "measurement"]:
        b = joblib.load(ROOT / "outputs" / "models" / f"{fs}__rf.joblib")
        proba = b["pipeline"].predict_proba(test[b["feature_cols"]])[:, 1]
        pred = (proba >= b["threshold"]).astype(int)
        df = test.copy()
        df["pred"] = pred
        df["y"] = test[TARGET].values
        df["age_group"] = pd.cut(df["Age"], bins=[13, 21, 30, 61],
                                 labels=["14-21", "22-30", "31-61"])
        for group_col in ["Gender", "age_group"]:
            for g, sub in df.groupby(group_col, observed=True):
                tn, fp, fn, tp = confusion_matrix(sub["y"], sub["pred"], labels=[0, 1]).ravel()
                out.append({
                    "feature_set": fs, "group_type": group_col, "group": str(g),
                    "n": int(len(sub)),
                    "obesity_rate": round(float(sub["y"].mean()), 3),
                    "accuracy": round(float(accuracy_score(sub["y"], sub["pred"])), 4),
                    "f1": round(float(f1_score(sub["y"], sub["pred"], zero_division=0)), 4),
                    "false_alarm_rate": round(float(fp / (fp + tn)) if (fp + tn) else 0.0, 4),
                    "miss_rate": round(float(fn / (fn + tp)) if (fn + tp) else 0.0, 4),
                })
    return out


def calibration(trainval, val, test):
    """在验证集上学校准映射（等张回归 / Platt 缩放），测试集只评估。"""
    out = []
    for fs in ["lifestyle", "measurement"]:
        b = joblib.load(ROOT / "outputs" / "models" / f"{fs}__rf.joblib")
        cols = b["feature_cols"]
        p_val = b["pipeline"].predict_proba(val[cols])[:, 1]
        p_test = b["pipeline"].predict_proba(test[cols])[:, 1]
        y_val = val[TARGET].values
        y_test = test[TARGET].values

        brier_before = brier_score_loss(y_test, p_test)
        # 等张回归校准
        iso = IsotonicRegression(out_of_bounds="clip").fit(p_val, y_val)
        p_iso = iso.predict(p_test)
        brier_iso = brier_score_loss(y_test, p_iso)
        # Platt 缩放（对 logit 做逻辑回归）
        eps = 1e-6
        pc = np.clip(p_val, eps, 1 - eps)
        logit = np.log(pc / (1 - pc)).reshape(-1, 1)
        platt = LogisticRegression().fit(logit, y_val)
        pct = np.clip(p_test, eps, 1 - eps)
        p_platt = platt.predict_proba(np.log(pct / (1 - pct)).reshape(-1, 1))[:, 1]
        brier_platt = brier_score_loss(y_test, p_platt)

        # 选验证集上表现更好的校准器
        iso_val_brier = brier_score_loss(y_val, iso.predict(p_val))
        platt_val_brier = brier_score_loss(y_val, platt.predict_proba(logit)[:, 1])
        best = "isotonic" if iso_val_brier <= platt_val_brier else "platt"
        brier_after = brier_iso if best == "isotonic" else brier_platt
        p_after = p_iso if best == "isotonic" else p_platt

        out.append({"feature_set": fs,
                    "brier_before": round(float(brier_before), 4),
                    "brier_isotonic": round(float(brier_iso), 4),
                    "brier_platt": round(float(brier_platt), 4),
                    "chosen_calibrator": best,
                    "brier_after": round(float(brier_after), 4)})
        print(f"[CAL] {fs:11s} Brier before={brier_before:.4f} -> after({best})={brier_after:.4f}")

        # 校准曲线
        fig, ax = plt.subplots(figsize=(5.6, 5.0))
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
        for prob, name, color in [(p_test, f"Before (Brier={brier_before:.3f})", "#D85A30"),
                                  (p_after, f"After {best} (Brier={brier_after:.3f})", "#1D9E75")]:
            bins = np.linspace(0, 1, 11)
            idx = np.digitize(prob, bins) - 1
            xs, ys = [], []
            for i in range(10):
                m = idx == i
                if m.sum() >= 15:
                    xs.append(prob[m].mean())
                    ys.append(y_test[m].mean())
            ax.plot(xs, ys, "o-", color=color, lw=1.8, ms=5, label=name)
        ax.set_xlabel("Predicted probability")
        ax.set_ylabel("Observed obesity frequency")
        ax.set_title(f"Calibration curve - {fs}")
        ax.legend(fontsize=9)
        ax.grid(alpha=.3)
        plt.tight_layout()
        plt.savefig(FIG / f"calibration_{fs}.png", dpi=150)
        plt.close()
    return out


def plot_cv(cv):
    labels = [f"{r['feature_set']}\n{r['model']}" for r in cv]
    means = [r["cv_f1_mean"] for r in cv]
    stds = [r["cv_f1_std"] for r in cv]
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    colors = ["#4C72B0", "#4C72B0", "#D85A30", "#D85A30"]
    ax.bar(range(len(cv)), means, yerr=stds, capsize=6, color=colors, alpha=.85)
    ax.set_xticks(range(len(cv)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("F1 score (5-fold CV, mean ± std)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Cross-validated F1 — single split is not a fluke")
    ax.grid(axis="y", alpha=.3)
    for i, (m, s) in enumerate(zip(means, stds)):
        ax.text(i, m + s + 0.02, f"{m:.3f}±{s:.3f}", ha="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG / "cv_f1.png", dpi=150)
    plt.close()


def plot_fairness(fair):
    life = [r for r in fair if r["feature_set"] == "lifestyle"]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    for ax, gtype, title in [(axes[0], "Gender", "By gender"),
                             (axes[1], "age_group", "By age group")]:
        rows = [r for r in life if r["group_type"] == gtype]
        groups = [r["group"] for r in rows]
        x = np.arange(len(groups))
        w = 0.27
        ax.bar(x - w, [r["accuracy"] for r in rows], w, label="Accuracy", color="#4C72B0")
        ax.bar(x, [r["false_alarm_rate"] for r in rows], w, label="False-alarm rate", color="#EF9F27")
        ax.bar(x + w, [r["miss_rate"] for r in rows], w, label="Miss rate", color="#D85A30")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{g}\n(n={r['n']})" for g, r in zip(groups, rows)], fontsize=9)
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=.3)
    plt.suptitle("Fairness check — lifestyle-only Random Forest on test set", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIG / "fairness.png", dpi=150)
    plt.close()


def main():
    t0 = time.time()
    train = pd.read_csv(SPLIT / "train.csv")
    val = pd.read_csv(SPLIT / "val.csv")
    test = pd.read_csv(SPLIT / "test.csv")
    trainval = pd.concat([train, val], ignore_index=True)

    print("=== 5 折交叉验证 ===")
    cv = cross_validate(trainval)
    plot_cv(cv)

    print("\n=== 公平性分析 ===")
    fair = fairness(test)
    plot_fairness(fair)
    for r in fair:
        if r["feature_set"] == "lifestyle":
            print(f"  {r['group_type']:10s} {r['group']:8s} n={r['n']:5d} "
                  f"acc={r['accuracy']:.3f} F1={r['f1']:.3f} "
                  f"false-alarm={r['false_alarm_rate']:.3f} miss={r['miss_rate']:.3f}")

    print("\n=== 概率校准 ===")
    cal = calibration(trainval, val, test)

    result = {"cross_validation": cv, "fairness": fair, "calibration": cal,
              "runtime_sec": round(time.time() - t0, 1)}
    with open(MET / "robustness.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n已保存 -> {MET / 'robustness.json'}  用时 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
