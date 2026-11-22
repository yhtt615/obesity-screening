"""
SHAP (SHapley Additive exPlanations) 可解释性分析
运行: python src/explain_shap.py
产物: outputs/metrics/shap_importance.json, outputs/figures/shap_global.png, shap_local.png

说明：SHAP 描述的是模型内部各特征对预测分数的贡献，是预测关联，不是因果。
"""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "outputs" / "figures"
MET = ROOT / "outputs" / "metrics"
SEED = 42
TARGET = "obesity_binary"

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


def raw_names(feature_names_out, cols):
    """把 One-Hot 展开后的列名映射回原始特征名。"""
    cols_sorted = sorted(cols, key=len, reverse=True)
    out = []
    for n in feature_names_out:
        core = n.split("__", 1)[1] if "__" in n else n
        matched = core
        for c in cols_sorted:
            if core == c or core.startswith(c + "_"):
                matched = c
                break
        out.append(matched)
    return out


def get_shap(pipe, X):
    prep = pipe[:-1]
    rf = pipe.named_steps["clf"]
    Xt = prep.transform(X)
    Xt = np.asarray(Xt.todense()) if hasattr(Xt, "todense") else np.asarray(Xt)
    explainer = shap.TreeExplainer(rf)
    sv = explainer.shap_values(Xt)
    if isinstance(sv, list):
        sv = sv[1]              # 正类（肥胖）
    elif sv.ndim == 3:
        sv = sv[:, :, 1]
    base = explainer.expected_value
    if isinstance(base, (list, np.ndarray)):
        base = float(np.asarray(base).ravel()[-1])
    names = raw_names(prep.get_feature_names_out(), X.columns.tolist())
    return sv, float(base), names


def aggregate(sv, names):
    """把同一原始特征的多个 dummy 列的 SHAP 贡献加总。"""
    df = pd.DataFrame(sv, columns=names)
    return df.T.groupby(level=0).sum().T


def main():
    test = pd.read_csv(ROOT / "data" / "split" / "test.csv")
    out = {}

    for fs in ["lifestyle", "measurement"]:
        b = joblib.load(ROOT / "outputs" / "models" / f"{fs}__rf.joblib")
        pipe = b["pipeline"]
        cols = b["feature_cols"]
        sample = test.sample(300, random_state=SEED)
        sv, base, names = get_shap(pipe, sample[cols])
        agg = aggregate(sv, names)

        importance = agg.abs().mean().sort_values(ascending=False)
        out[fs] = {k: round(float(v), 5) for k, v in importance.items()}
        print(f"\n=== {fs} 全局 SHAP 重要性（mean |SHAP|）===")
        for k, v in importance.items():
            print(f"  {k:32s} {v:.5f}")

        # 全局条形图
        top = importance.head(14)
        fig, ax = plt.subplots(figsize=(7.4, 5.2))
        ax.barh([PRETTY.get(k, k) for k in top.index][::-1], top.values[::-1], color="#4C72B0")
        ax.set_xlabel("Mean |SHAP value| (impact on model output)")
        ax.set_title(f"Global SHAP importance - {fs}")
        ax.grid(axis="x", alpha=.3)
        plt.tight_layout()
        plt.savefig(FIG / f"shap_global_{fs}.png", dpi=150)
        plt.close()

        # 两个真实个体的局部解释
        cases = []
        for want_id, tag in [(16056, "Obesity_Type_III"), (6000, "Normal_Weight")]:
            row = test[test["id"] == want_id]
            if len(row) == 0:
                continue
            sv1, base1, names1 = get_shap(pipe, row[cols])
            agg1 = aggregate(sv1, names1).iloc[0].sort_values()
            cases.append((tag, agg1, base1, float(row["NObeyesdad"].iloc[0] == row["NObeyesdad"].iloc[0])))

        if cases:
            fig, axes = plt.subplots(1, len(cases), figsize=(6.4 * len(cases), 4.8))
            if len(cases) == 1:
                axes = [axes]
            for ax, (tag, contrib, base1, _) in zip(axes, cases):
                show = pd.concat([contrib.head(5), contrib.tail(5)]).drop_duplicates()
                colors = ["#D85A30" if v > 0 else "#4C72B0" for v in show.values]
                ax.barh([PRETTY.get(k, k) for k in show.index], show.values, color=colors)
                ax.axvline(0, color="k", lw=.8)
                ax.set_title(f"Individual explanation: {tag}\n(orange pushes toward obesity, blue away)")
                ax.set_xlabel("SHAP contribution to prediction")
                ax.grid(axis="x", alpha=.3)
            plt.tight_layout()
            plt.savefig(FIG / f"shap_local_{fs}.png", dpi=150)
            plt.close()

    with open(MET / "shap_importance.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n已保存 -> {MET / 'shap_importance.json'}")


if __name__ == "__main__":
    main()
