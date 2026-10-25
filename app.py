"""
Step 4 - 问卷式演示界面
运行: streamlit run app.py
说明: 输入为虚构示例，仅用于演示，不可用于任何医学判断。
"""
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "outputs" / "models"

LIFESTYLE = ["Gender", "Age", "family_history_with_overweight", "FAVC", "FCVC",
             "NCP", "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE", "CALC", "MTRANS"]

st.set_page_config(page_title="Obesity Screening Demo", page_icon="🩺", layout="wide")
st.title("Lifestyle-Based Obesity Screening — Demo")
st.caption("Course project · 吴炳言 / 杨皓童 / 杜沛霖 · "
           "对虚构示例的演示，**不能用于医学诊断**")

st.warning("本工具仅用于课程演示。模型基于公开数据集的**当前状态**标签训练，"
           "不是对未来肥胖风险的预测，也不能作为任何临床决策依据。", icon="⚠️")


@st.cache_resource
def load_models():
    return {
        "lifestyle": joblib.load(MODEL_DIR / "lifestyle__rf.joblib"),
        "measurement": joblib.load(MODEL_DIR / "measurement__rf.joblib"),
        "lifestyle_mc": joblib.load(MODEL_DIR / "lifestyle__multiclass.joblib"),
        "measurement_mc": joblib.load(MODEL_DIR / "measurement__multiclass.joblib"),
    }


models = load_models()

with st.form("questionnaire"):
    st.subheader("第一步 · 生活方式问卷（两个模型都需要）")
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.selectbox("性别 Gender", ["Male", "Female"])
        age = st.slider("年龄 Age", 14, 61, 24)
        fam_hist = st.selectbox("家族是否有超重史 Family history",
                                ["1", "0"], format_func=lambda x: "是 Yes" if x == "1" else "否 No")
        favc = st.selectbox("是否常吃高热量食物 FAVC",
                            ["1", "0"], format_func=lambda x: "是 Yes" if x == "1" else "否 No")
        fcvc = st.slider("蔬菜摄入频率 FCVC (1=低, 3=高)", 1.0, 3.0, 2.5, 0.1)
    with c2:
        ncp = st.slider("每日主餐次数 NCP", 1.0, 4.0, 3.0, 0.1)
        caec = st.selectbox("两餐之间加餐频率 CAEC", ["no", "Sometimes", "Frequently", "Always"])
        smoke = st.selectbox("是否吸烟 SMOKE", ["0", "1"],
                             format_func=lambda x: "是 Yes" if x == "1" else "否 No")
        ch2o = st.slider("每日饮水 CH2O (1=少, 3=多)", 1.0, 3.0, 2.0, 0.1)
        scc = st.selectbox("是否监测热量摄入 SCC", ["0", "1"],
                           format_func=lambda x: "是 Yes" if x == "1" else "否 No")
    with c3:
        faf = st.slider("运动频率 FAF (0=不运动, 3=高)", 0.0, 3.0, 1.0, 0.1)
        tue = st.slider("每日屏幕/电子设备时长 TUE (0-2)", 0.0, 2.0, 0.6, 0.1)
        calc = st.selectbox("饮酒频率 CALC", ["no", "Sometimes", "Frequently"])
        mtrans = st.selectbox("主要通勤方式 MTRANS",
                              ["Public_Transportation", "Walking", "Automobile",
                               "Motorbike", "Bike"])

    st.subheader("第二步 · 身体测量值（仅含测量值模型使用，可留默认）")
    m1, m2 = st.columns(2)
    with m1:
        height = st.number_input("身高 Height (m)", 1.45, 2.10, 1.70, 0.01)
    with m2:
        weight = st.number_input("体重 Weight (kg)", 39.0, 170.0, 70.0, 0.5)

    submitted = st.form_submit_button("预测 / Predict", use_container_width=True)

if submitted:
    row = {"Gender": gender, "Age": age, "family_history_with_overweight": fam_hist,
           "FAVC": favc, "FCVC": fcvc, "NCP": ncp, "CAEC": caec, "SMOKE": smoke,
           "CH2O": ch2o, "SCC": scc, "FAF": faf, "TUE": tue, "CALC": calc,
           "MTRANS": mtrans, "Height": height, "Weight": weight,
           "BMI": weight / (height ** 2)}
    # 这四列在数据集中是 0/1 整数；若保持字符串，OneHotEncoder 会当未知类别
    # 静默编码为全 0，导致预测错误（实测 0.978 -> 0.486）。必须转 int。
    for c in ["family_history_with_overweight", "FAVC", "SMOKE", "SCC"]:
        row[c] = int(row[c])
    df = pd.DataFrame([row])

    st.divider()
    st.subheader("预测结果")

    colA, colB = st.columns(2)

    # ---- 生活方式模型 ----
    b = models["lifestyle"]
    p = b["pipeline"].predict_proba(df[b["feature_cols"]])[0][1]
    thr = b["threshold"]
    label = "肥胖类 (Obesity I-III)" if p >= thr else "非肥胖类 (normal / overweight / underweight)"
    with colA:
        st.markdown("#### A. 生活方式模型（不含身高体重）")
        st.metric("预测类别", label)
        st.metric("肥胖类概率", f"{p:.1%}")
        st.progress(float(p))
        st.caption(f"判定阈值 {thr:.2f}（在验证集上按 F1 最优选取）")
        mc = models["lifestyle_mc"]
        proba_mc = mc["pipeline"].predict_proba(df[mc["feature_cols"]])[0]
        classes = mc["pipeline"].classes_
        st.caption("七类细分概率：")
        st.dataframe(pd.DataFrame({"类别": classes, "概率": proba_mc})
                     .sort_values("概率", ascending=False)
                     .assign(概率=lambda d: (d["概率"] * 100).round(1).astype(str) + "%")
                     .reset_index(drop=True), hide_index=True, use_container_width=True)

    # ---- 含测量值模型 ----
    b = models["measurement"]
    p2 = b["pipeline"].predict_proba(df[b["feature_cols"]])[0][1]
    thr2 = b["threshold"]
    label2 = "肥胖类 (Obesity I-III)" if p2 >= thr2 else "非肥胖类 (normal / overweight / underweight)"
    with colB:
        st.markdown("#### B. 含测量值模型（含身高/体重/BMI）")
        st.metric("预测类别", label2)
        st.metric("肥胖类概率", f"{p2:.1%}")
        st.progress(float(p2))
        st.caption(f"判定阈值 {thr2:.2f}")
        mc = models["measurement_mc"]
        proba_mc = mc["pipeline"].predict_proba(df[mc["feature_cols"]])[0]
        classes = mc["pipeline"].classes_
        st.caption("七类细分概率：")
        st.dataframe(pd.DataFrame({"类别": classes, "概率": proba_mc})
                     .sort_values("概率", ascending=False)
                     .assign(概率=lambda d: (d["概率"] * 100).round(1).astype(str) + "%")
                     .reset_index(drop=True), hide_index=True, use_container_width=True)

    st.divider()
    st.caption(f"当前输入对应的 BMI = {weight / (height ** 2):.1f}。"
               f"注意：含测量值模型在测试集上 AUC 更高（0.996 vs 0.964），"
               f"但排列重要性显示它几乎只依赖 BMI/体重，生活方式信息贡献很小——"
               f"这正是本项目同时报告两套模型的原因。")

    with st.expander("查看模型输入的具体特征值"):
        st.dataframe(df.T.rename(columns={0: "value"}), use_container_width=True)
