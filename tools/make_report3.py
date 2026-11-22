"""
生成第三次项目进度报告：一页 A4 PDF，英文。
运行: python tools/make_report3.py
产物: outputs/Third_Progress_Report.pdf
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "Third_Progress_Report.pdf"

BLUE = colors.HexColor("#2F6FB2")
DARK = colors.HexColor("#1A2332")
MUTED = colors.HexColor("#5B6B82")
LIGHT = colors.HexColor("#EEF3FA")
ACCENT = colors.HexColor("#B4542A")

REPO = "https://github.com/yhtt615/obesity-screening"


def styles():
    base = dict(fontName="Helvetica", fontSize=8.4, leading=10.6, textColor=DARK,
                alignment=TA_JUSTIFY)
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=15,
                                leading=18, textColor=BLUE, alignment=TA_LEFT),
        "meta": ParagraphStyle("meta", fontName="Helvetica", fontSize=7.6, leading=9.6,
                               textColor=MUTED, alignment=TA_LEFT),
        "head": ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=9.6, leading=12,
                               textColor=BLUE, spaceBefore=5, spaceAfter=2, alignment=TA_LEFT),
        "body": ParagraphStyle("body", **base),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=7.8, leading=9.8,
                                textColor=DARK, alignment=TA_LEFT),
        "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=7.8, leading=9.4,
                               textColor=DARK, alignment=TA_LEFT),
        "cellh": ParagraphStyle("cellh", fontName="Helvetica-Bold", fontSize=7.8, leading=9.4,
                                textColor=BLUE, alignment=TA_LEFT),
    }


S = styles()

SECTIONS = [
    ("1. Models",
     "Three classifiers, each trained on two feature sets &mdash; <b>lifestyle-only</b> (14 features, "
     "height/weight/BMI excluded) and <b>measurement-inclusive</b> (17 features). "
     "<b>(i) Majority-class baseline (Dummy Classifier):</b> always predicts the most frequent class; it carries "
     "no information and only defines the floor a real model must beat. "
     "<b>(ii) Logistic Regression (LR):</b> a linear model that learns one weight per feature and outputs a "
     "probability through the logistic (sigmoid) function; regularisation strength C in {0.1, 1, 10} penalises "
     "large weights, with optional class weighting (6 configurations). "
     "<b>(iii) Random Forest (RF):</b> an ensemble of 400 decision trees. Each tree is grown on a bootstrap "
     "resample (sampling with replacement) of the training data and may consider only sqrt(p) (about 5) randomly "
     "offered features at each split, where p is the number of encoded features; the 400 trees then vote, and the "
     "fraction voting &ldquo;obesity&rdquo; is the predicted probability. RF was tuned over depth, minimum leaf "
     "size and class weighting (8 configurations). "
     "<b>New since report 2:</b> an <b>Isotonic Regression calibrator</b> &mdash; a non-parametric, monotonically "
     "increasing mapping fitted on validation predictions &mdash; now sits on top of the RF scores so that an output "
     "of 0.7 genuinely corresponds to about 70 % of such cases being obese."),

    ("2. Current pipeline",
     "Five scripts, run in order. <b>(1) prepare_data.py</b> verifies the schema, repairs three label defects, "
     "derives BMI (Body Mass Index) and writes a stratified 70/15/15 split (seed 42). "
     "<b>(2) train.py</b> wraps StandardScaler and One-Hot Encoding inside a scikit-learn Pipeline fitted on "
     "training data only, trains 30 candidate pipelines, and selects hyper-parameters and the decision threshold "
     "on the validation set. <b>(3) evaluate.py</b> reads the held-out test set exactly once and produces every "
     "reported metric and figure. <b>(4) robustness.py (new)</b> adds 5-fold stratified cross-validation on "
     "train+validation, subgroup fairness evaluation and calibration. <b>(5) explain_shap.py (new)</b> adds "
     "TreeSHAP (SHapley Additive exPlanations) global and per-record explanations. A dependency-free web demo "
     "(predict_server.py, Python standard-library HTTP server) serves both models through a questionnaire."),

    ("3. Progress and evidence",
     "Cross-validated F1 (mean &plusmn; std over 5 folds) is shown in the table below. The lifestyle Random Forest "
     "reaches ROC-AUC 0.963 &plusmn; 0.001, so the earlier single-split score (0.964) was not a lucky split. "
     "Calibration (Brier score, lower is better) improves the lifestyle model from 0.0768 to 0.0753; the "
     "measurement model was already well calibrated (0.0189). SHAP confirms the lifestyle model leans on family "
     "history, age, daily water intake, snacking and vegetable intake, whereas the measurement model is dominated "
     "by BMI and weight (mean |SHAP| 0.226 and 0.166, versus 0.039 for the next feature). "
     "Evidence on disk: src/robustness.py, src/explain_shap.py, "
     "outputs/metrics/robustness.json and shap_importance.json, and figures cv_f1.png, fairness.png, "
     "calibration_*.png, shap_global_*.png, shap_local_*.png."),

    ("4. Problems encountered and how we addressed them",
     "<b>(a) Silent type mismatch:</b> the four yes/no fields are integers in the data but arrive as text from a "
     "web form, so One-Hot Encoding treated &ldquo;1&rdquo; as an unseen category and encoded it as all zeros "
     "&mdash; no error, no warning, and one record dropped from 0.978 to 0.486. Fixed by explicit integer casting. "
     "<b>(b) Out-of-distribution inputs:</b> an all-extreme hand-made demo profile scored only 0.25 despite BMI "
     "38.5, because that combination does not occur in the training data; demo presets now use real records. "
     "<b>(c) Fairness:</b> the lifestyle model misses 38.7 % of obese cases in the 14&ndash;21 age group (versus "
     "5.3 % at ages 22&ndash;30) and raises more false alarms for men (0.114) than women (0.067). We now report "
     "subgroup metrics explicitly instead of a single average. "
     "<b>(d) Minor miscalibration</b> in the lifestyle model, addressed with the isotonic calibrator above."),

    ("5. Remaining work",
     "Reduce the young-group miss rate (group-specific thresholds or class reweighting, then re-validate on held-out "
     "data); finalise the written report with the new robustness, fairness and SHAP figures; rehearse the five-minute "
     "presentation; and, optionally, host the demo online for live questions. We will keep the lifestyle-only model "
     "as the interpretable headline result and the measurement model purely as a comparison."),
]

CV_TABLE = [
    ["Feature set", "Model", "CV F1 (mean ± std)", "CV ROC-AUC (mean ± std)"],
    ["Lifestyle-only", "Logistic Regression", "0.814 ± 0.003", "0.891 ± 0.004"],
    ["Lifestyle-only", "Random Forest", "0.893 ± 0.004", "0.963 ± 0.001"],
    ["Measurement-inclusive", "Logistic Regression", "0.964 ± 0.002", "0.994 ± 0.001"],
    ["Measurement-inclusive", "Random Forest", "0.971 ± 0.002", "0.996 ± 0.001"],
]


def main():
    doc = SimpleDocTemplate(str(OUT), pagesize=A4,
                            leftMargin=13 * mm, rightMargin=13 * mm,
                            topMargin=11 * mm, bottomMargin=10 * mm,
                            title="Third Project Progress Report",
                            author="Wu Bingyan, Yang Haotong, Du Peilin")
    story = []
    story.append(Paragraph("Third Project Progress Report", S["title"]))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "Project: Lifestyle-Based Obesity Screening with Lightweight Machine Learning<br/>"
        "Team: Wu Bingyan, Yang Haotong, Du Peilin &nbsp;&nbsp;|&nbsp;&nbsp; Date: 22 November 2026<br/>"
        f"Repository: {REPO}", S["meta"]))
    story.append(Spacer(1, 3))

    for i, (head, body) in enumerate(SECTIONS):
        story.append(Paragraph(head, S["head"]))
        story.append(Paragraph(body, S["body"]))
        if head.startswith("3."):
            story.append(Spacer(1, 3))
            data = [[Paragraph(c, S["cellh"] if r == 0 else S["cell"]) for c in row]
                    for r, row in enumerate(CV_TABLE)]
            t = Table(data, colWidths=[38 * mm, 40 * mm, 46 * mm, 50 * mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FC")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E0EC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t)
            story.append(Spacer(1, 3))

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Note: all results describe predictive association, not causation. This is a screening aid for current "
        "status, not a medical diagnosis or a prediction of future risk. One member submits on behalf of the group.",
        S["small"]))

    doc.build(story)
    print(f"已生成: {OUT}")

    # 检查页数
    try:
        from pypdf import PdfReader
        n = len(PdfReader(str(OUT)).pages)
        print(f"页数: {n}")
    except ImportError:
        print("（未安装 pypdf，无法自动检查页数）")


if __name__ == "__main__":
    main()
