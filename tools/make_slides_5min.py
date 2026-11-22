"""Generate the concise five-minute progress presentation."""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "outputs" / "figures"
OUT = ROOT / "outputs" / "Second_Progress_Report_5min.pptx"

BLUE = RGBColor(0x2F, 0x6F, 0xB2)
DARK = RGBColor(0x1A, 0x23, 0x32)
MUTED = RGBColor(0x5B, 0x6B, 0x82)
LIGHT = RGBColor(0xEE, 0xF3, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ACCENT = RGBColor(0xD8, 0x5A, 0x30)
W = Inches(13.333)
H = Inches(7.5)
FONT = "Segoe UI"

prs = Presentation()
prs.slide_width = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]


def add_slide(title, subtitle=""):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, 0, 0, W, Inches(1.08))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    bar.shadow.inherit = False
    tf = bar.text_frame
    tf.margin_left = Inches(0.55)
    tf.margin_top = Inches(0.12)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT
    if subtitle:
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = RGBColor(0xCF, 0xE2, 0xF5)
        p2.font.name = FONT
    return s


def add_text(s, value, x, y, w, h, size=13, bold=False, color=DARK,
             align=PP_ALIGN.LEFT, italic=False):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = value
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = FONT
    p.alignment = align
    p.italic = italic
    return box


def add_bullets(s, items, x, y, w, h, size=13, gap=9):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(item, tuple):
            head, body = item
            r = p.add_run()
            r.text = head
            r.font.bold = True
            r.font.size = Pt(size)
            r.font.color.rgb = DARK
            r.font.name = FONT
            r = p.add_run()
            r.text = body
            r.font.size = Pt(size)
            r.font.color.rgb = DARK
            r.font.name = FONT
        else:
            p.text = "•  " + item
            p.font.size = Pt(size)
            p.font.color.rgb = DARK
            p.font.name = FONT
        p.space_after = Pt(gap)
        p.line_spacing = 1.05
    return box


def add_table(s, data, x, y, w, h, widths, size=12):
    shape = s.shapes.add_table(len(data), len(data[0]), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    for i, width in enumerate(widths):
        tbl.columns[i].width = Inches(width)
    for r, row in enumerate(data):
        for c, value in enumerate(row):
            cell = tbl.cell(r, c)
            cell.text = str(value)
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(size)
            p.font.name = FONT
            p.font.bold = (r == 0)
            p.font.color.rgb = BLUE if r == 0 else DARK
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT if r == 0 else (
                RGBColor(0xF7, 0xF9, 0xFC) if r % 2 == 0 else WHITE)
    return tbl


def add_code_box(s, lines, x, y, w, h):
    box = s.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = LIGHT
    box.line.color.rgb = BLUE
    box.shadow.inherit = False
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.18)
    tf.margin_top = Inches(0.08)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(11.5)
        p.font.name = FONT
        p.font.color.rgb = DARK
        p.space_after = Pt(4)
    return box


def footer(s, number):
    add_text(s, f"{number} / 8", 12.35, 7.02, 0.55, 0.25, size=10, color=MUTED,
             align=PP_ALIGN.RIGHT)


# 1 — Title, 20 seconds
s = prs.slides.add_slide(BLANK)
band = s.shapes.add_shape(1, 0, 0, W, Inches(3.0))
band.fill.solid()
band.fill.fore_color.rgb = BLUE
band.line.fill.background()
band.shadow.inherit = False
tf = band.text_frame
tf.margin_left = Inches(0.8)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]
p.text = "Second Project Progress Report"
p.font.size = Pt(17)
p.font.bold = True
p.font.color.rgb = RGBColor(0xCF, 0xE2, 0xF5)
p.font.name = FONT
p = tf.add_paragraph()
p.text = "Lifestyle-Based Obesity Screening\nwith Lightweight Machine Learning"
p.font.size = Pt(32)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = FONT
add_bullets(s, [
    ("Team: ", "Wu Bingyan  ·  Yang Haotong  ·  Du Peilin"),
    ("Date: ", "26 October 2026  ·  Five-minute presentation"),
    ("Objective: ", "predict a person’s current obesity category from lifestyle and demographic information."),
], 0.85, 3.55, 11.7, 1.8, size=15, gap=13)
add_text(s, "Scope: a screening aid, not a medical diagnosis or a prediction of future risk.",
         0.85, 5.75, 11.7, 0.55, size=14, color=ACCENT, italic=True)
footer(s, 1)

# 2 — Data, 40 seconds
s = add_slide("1. Data and quality checks", "20,758 records × 18 columns · no missing values · no duplicate rows")
add_bullets(s, [
    ("Source: ", "Kaggle “Obesity Risk” dataset, distributed through Heywhale."),
    ("Inputs: ", "gender, age, height, weight, family history, and eleven lifestyle variables covering "
                 "diet, water intake, physical activity, screen time, smoking, alcohol and transport."),
    ("Target: ", "seven current obesity levels; the main task merges Obesity types I–III against all other levels."),
    ("Repairs: ", "two corrupted names were fixed, and the symbol “0” in two lifestyle fields was restored to “no”."),
    ("Split: ", "stratified 70 % training / 15 % validation / 15 % test = 14,530 / 3,114 / 3,114 records."),
    ("Key finding: ", "mean BMI (Body Mass Index = weight in kilograms divided by height in metres squared) "
                       "rises from 17.6 to 41.8 across the seven classes, so the labels are BMI-derived."),
], 0.65, 1.45, 12.0, 5.3, size=14, gap=13)
footer(s, 2)

# 3 — Design and models, 45 seconds
s = add_slide("2. Experiment design and models", "Two feature sets, three models, and a leakage-free protocol")
add_text(s, "Experiment design", 0.65, 1.4, 5.8, 0.4, size=16, bold=True, color=BLUE)
add_bullets(s, [
    ("Lifestyle-only: ", "no height, weight or BMI."),
    ("Measurement-inclusive: ", "adds height, weight and BMI for comparison."),
    ("Protocol: ", "preprocessing is fitted on training data only; validation data select settings and the "
                   "decision threshold; the test set is evaluated once at the end."),
], 0.65, 1.95, 5.8, 3.5, size=13.5, gap=13)
add_text(s, "Models already trained", 6.85, 1.4, 5.8, 0.4, size=16, bold=True, color=BLUE)
add_bullets(s, [
    ("Majority baseline: ", "always predicts the most frequent class."),
    ("Logistic Regression (LR): ", "a linear probability model; six configurations tested."),
    ("Random Forest (RF): ", "400 decision trees voting together; eight configurations tested."),
    ("Workload: ", "30 fitted pipelines in 24 seconds on a laptop CPU (Central Processing Unit)."),
], 6.85, 1.95, 5.8, 3.8, size=13.5, gap=13)
add_text(s, "Why two feature sets? The measurement model may score higher simply by reading the BMI-derived label.",
         0.65, 6.15, 12.0, 0.55, size=13, color=ACCENT)
footer(s, 3)

# 4 — Results, 50 seconds
s = add_slide("3. Main results", "Held-out test set: 3,114 records, evaluated once")
add_table(s, [
    ["Feature set", "Model", "Accuracy", "F1 score", "ROC-AUC"],
    ["Lifestyle-only", "Majority baseline", "0.508", "0.000", "0.500"],
    ["Lifestyle-only", "Logistic Regression", "0.802", "0.824", "0.902"],
    ["Lifestyle-only", "Random Forest  ◄ main", "0.897", "0.894", "0.964"],
    ["Measurement-inclusive", "Random Forest", "0.977", "0.976", "0.996"],
], 0.75, 1.5, 11.85, 2.15, [3.3, 3.6, 1.65, 1.65, 1.65], size=13)
add_bullets(s, [
    ("F1 score: ", "the harmonic mean of precision and recall; it balances false alarms against missed cases."),
    ("ROC-AUC: ", "Receiver Operating Characteristic – Area Under the Curve; 0.5 is random and 1.0 is perfect ranking."),
    ("Seven-class extension: ", "72.7 % accuracy with lifestyle features and 90.0 % with measurements."),
], 0.75, 4.15, 11.85, 2.1, size=13, gap=10)
add_text(s, "Main result: a questionnaire-only model reaches F1 = 0.894 and ROC-AUC = 0.964.",
         0.75, 6.35, 11.85, 0.45, size=14, bold=True, color=BLUE)
footer(s, 4)

# 5 — Interpretation, 40 seconds
s = add_slide("4. What the models rely on",
              "Permutation importance = accuracy lost after shuffling one feature")
s.shapes.add_picture(str(FIG / "perm_lifestyle.png"), Inches(0.45), Inches(1.4), width=Inches(6.15))
s.shapes.add_picture(str(FIG / "perm_measurement.png"), Inches(6.75), Inches(1.4), width=Inches(6.15))
add_text(s, "Lifestyle model: age, family history, snacking, vegetables and high-calorie food lead.",
         0.5, 5.9, 6.05, 0.7, size=11.5, color=BLUE, align=PP_ALIGN.CENTER)
add_text(s, "Measurement model: BMI (0.153) and weight (0.131) dominate; the next feature is only 0.005.",
         6.8, 5.9, 6.05, 0.7, size=11.5, color=ACCENT, align=PP_ALIGN.CENTER)
add_text(s, "The higher measurement score is therefore largely a BMI shortcut. These are associations, not causes.",
         0.65, 6.65, 12.0, 0.45, size=12.5, color=DARK, align=PP_ALIGN.CENTER)
footer(s, 5)

# 6 — Evidence, 35 seconds
s = add_slide("5. Completed work and evidence", "Code, saved results, figures and a working prediction demo")
add_bullets(s, [
    ("Code completed: ", "prepare_data.py cleans and splits; train.py fits and tunes; evaluate.py produces "
                         "the final test metrics and figures."),
    ("Results saved: ", "three JSON (JavaScript Object Notation) files, seven figures, and trained pipelines "
                        "with preprocessing embedded."),
    ("Demo completed: ", "a questionnaire returns both models’ probabilities and seven-class distributions; "
                         "it can also compare predictions with known labels on real held-out records."),
], 0.65, 1.45, 12.0, 3.25, size=14, gap=14)
add_code_box(s, [
    "Reproduce:  python src/prepare_data.py  →  python src/train.py  →  python src/evaluate.py",
    "Run demo:   python -X utf8 predict_server.py   →   http://localhost:8501",
], 0.65, 5.15, 12.0, 1.15)
footer(s, 6)

# 7 — Problems, 40 seconds
s = add_slide("6. Problems encountered", "Three issues that changed our implementation")
add_bullets(s, [
    ("1. Corrupted labels: ", "a misspelt target column and class name were repaired before training; "
                              "otherwise a phantom class would have appeared."),
    ("2. Silent type mismatch: ", "web forms submit text, but four yes/no fields were integers during training. "
                                  "One-Hot Encoding (OHE = one 0/1 column per category) treated the text as unknown and encoded it as zeros. "
                                  "The same record scored 0.978 versus 0.486; explicit integer conversion fixed it."),
    ("3. Out-of-distribution inputs: ", "an extreme hand-made demo profile scored only 0.25 despite BMI = 38.5 "
                                        "because that combination was unlike the training data. We replaced the presets with real records."),
], 0.65, 1.5, 12.0, 4.8, size=14, gap=18)
add_text(s, "Lesson: a pipeline can run without errors and still produce invalid predictions — inputs must be tested, not assumed.",
         0.65, 6.35, 12.0, 0.55, size=13, color=ACCENT)
footer(s, 7)

# 8 — Next steps and takeaway, 30 seconds
s = add_slide("7. Next steps and takeaway", "From a working baseline to a more carefully validated final report")
add_bullets(s, [
    ("Fairness: ", "compare errors by gender and age group."),
    ("SHAP (SHapley Additive exPlanations): ", "explain individual predictions, not only global importance."),
    ("Calibration: ", "check whether a predicted 70 % probability means about seven correct cases in ten."),
    ("Cross-validation: ", "repeat the data split to measure variation rather than relying on one split."),
], 0.65, 1.45, 12.0, 3.3, size=14, gap=13)
box = s.shapes.add_shape(1, Inches(0.65), Inches(5.15), Inches(12.0), Inches(1.35))
box.fill.solid()
box.fill.fore_color.rgb = BLUE
box.line.fill.background()
box.shadow.inherit = False
tf = box.text_frame
tf.word_wrap = True
tf.margin_left = Inches(0.25)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]
p.text = ("Takeaway: without height, weight or BMI, Random Forest reaches F1 = 0.894 and ROC-AUC = 0.964. "
          "We report the measurement model separately because its higher score mostly comes from reading BMI.")
p.font.size = Pt(15)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = FONT
footer(s, 8)

# Increase every text element uniformly for projection/readability.
FONT_SCALE = 1.15
for current_slide in prs.slides:
    frames = []
    for shape in current_slide.shapes:
        if shape.has_text_frame:
            frames.append(shape.text_frame)
        if shape.has_table:
            frames.extend(cell.text_frame for row in shape.table.rows for cell in row.cells)
    for frame in frames:
        for paragraph in frame.paragraphs:
            if paragraph.font.size:
                paragraph.font.size = Pt(paragraph.font.size.pt * FONT_SCALE)
            for run in paragraph.runs:
                if run.font.size:
                    run.font.size = Pt(run.font.size.pt * FONT_SCALE)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print(f"Generated: {OUT}")
print(f"Slides: {len(prs.slides)}")
