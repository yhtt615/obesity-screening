"""
生成答辩用幻灯片（英文，所有缩写均标注全称）
运行: python tools/make_slides.py
产物: outputs/Second_Progress_Report.pptx
"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "outputs" / "figures"
OUT = ROOT / "outputs" / "Second_Progress_Report.pptx"

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


def slide(title, kicker=None):
    s = prs.slides.add_slide(BLANK)
    bar = s.shapes.add_shape(1, 0, 0, W, Inches(1.15))
    bar.fill.solid()
    bar.fill.fore_color.rgb = BLUE
    bar.line.fill.background()
    bar.shadow.inherit = False
    tf = bar.text_frame
    tf.margin_left = Inches(0.55)
    tf.margin_top = Inches(0.14)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT
    if kicker:
        p2 = tf.add_paragraph()
        p2.text = kicker
        p2.font.size = Pt(12)
        p2.font.color.rgb = RGBColor(0xCF, 0xE2, 0xF5)
        p2.font.name = FONT
    return s


def text(s, text_, x, y, w, h, size=14, bold=False, color=DARK, align=PP_ALIGN.LEFT,
         italic=False, line=None):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text_
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = FONT
    p.italic = italic
    p.alignment = align
    if line:
        p.line_spacing = line
    return tb


def bullets(s, items, x, y, w, h, size=13, gap=6, color=DARK):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if isinstance(it, tuple):
            head, rest = it
            r = p.add_run()
            r.text = head
            r.font.bold = True
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.name = FONT
            r2 = p.add_run()
            r2.text = rest
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
            r2.font.name = FONT
        else:
            p.text = "•  " + it
            p.font.size = Pt(size)
            p.font.color.rgb = color
            p.font.name = FONT
        p.space_after = Pt(gap)
        p.line_spacing = 1.08
    return tb


def table(s, data, x, y, w, h, col_w=None, size=10.5, header_size=10.5):
    rows, cols = len(data), len(data[0])
    shp = s.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(h))
    t = shp.table
    if col_w:
        for i, cw in enumerate(col_w):
            t.columns[i].width = Inches(cw)
    for r in range(rows):
        for c in range(cols):
            cell = t.cell(r, c)
            cell.text = str(data[r][c])
            cell.margin_left = Inches(0.06)
            cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(header_size if r == 0 else size)
            p.font.name = FONT
            p.font.bold = (r == 0)
            p.font.color.rgb = DARK
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = LIGHT
                p.font.color.rgb = BLUE
            elif r % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xF7, 0xF9, 0xFC)
    return t


def footer(s, n):
    text(s, str(n), 12.6, 7.02, 0.5, 0.3, size=10, color=MUTED, align=PP_ALIGN.RIGHT)


# ============================== 1. Title ==============================
s = prs.slides.add_slide(BLANK)
band = s.shapes.add_shape(1, 0, 0, W, Inches(3.05))
band.fill.solid()
band.fill.fore_color.rgb = BLUE
band.line.fill.background()
band.shadow.inherit = False
tf = band.text_frame
tf.margin_left = Inches(0.8)
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
for txt, sz, col in [("Second Project Progress Report", Pt(17), RGBColor(0xCF, 0xE2, 0xF5)),
                     ("Lifestyle-Based Obesity Screening\nwith Lightweight Machine Learning",
                      Pt(33), WHITE)]:
    p = tf.paragraphs[0] if txt.startswith("Second") else tf.add_paragraph()
    p.text = txt
    p.font.size = sz
    p.font.bold = True
    p.font.color.rgb = col
    p.font.name = FONT

bullets(s, [
    ("Team: ", "Wu Bingyan  ·  Yang Haotong  ·  Du Peilin"),
    ("Date: ", "25 October 2026"),
    ("Dataset: ", "Kaggle “Obesity Risk” dataset, distributed via Heywhale — 20,758 records"),
    ("Code repository: ", "local Git repository initialised and committed; ready to push to GitHub"),
    ("Live demo: ", "http://localhost:8501  (interactive questionnaire, Python standard library only)"),
], 0.85, 3.55, 11.6, 2.4, size=14, gap=12)
text(s, "All abbreviations are spelled out on every slide.", 0.85, 6.45, 11.6, 0.4,
     size=12, color=MUTED, italic=True)

# ============================== 2. Dataset ==============================
s = slide("1. Data we are using", "Where it comes from, how big it is, and how it was split")
bullets(s, [
    ("Source: ", "Kaggle “Obesity Risk” dataset, distributed to us through Heywhale; "
                 "file name obesity_level.csv (CSV = Comma-Separated Values, a plain-text table)."),
    ("Size: ", "20,758 records (rows) × 18 columns. No missing values anywhere; "
               "no duplicate records (checked on all columns except the identifier)."),
    ("Content: ", "demographic information (gender, age), body measurements (height, weight), "
                  "family history of overweight, and eleven lifestyle / behavioural variables."),
    ("Target (label to predict): ", "NObeyesdad — the person’s obesity level, with 7 classes: "
                                    "Insufficient weight, Normal weight, Overweight level I, "
                                    "Overweight level II, Obesity type I, II and III."),
    ("Class balance: ", "after merging into the binary task the data are close to perfectly balanced — "
                        "49.2 % obesity versus 50.8 % non-obesity, so accuracy is not misleading."),
    ("Split: ", "stratified 70 % training / 15 % validation / 15 % test "
                "= 14,530 / 3,114 / 3,114 records, with a fixed random seed of 42."),
], 0.6, 1.45, 12.2, 4.4, size=13.5, gap=11)

box = s.shapes.add_shape(1, Inches(0.6), Inches(5.95), Inches(12.15), Inches(0.95))
box.fill.solid()
box.fill.fore_color.rgb = LIGHT
box.line.color.rgb = BLUE
box.shadow.inherit = False
tb = box.text_frame
tb.word_wrap = True
tb.margin_left = Inches(0.2)
p = tb.paragraphs[0]
p.text = ("“Stratified” split = we sampled so that each of the 7 classes keeps the same proportion in "
          "the training, validation and test parts. This prevents one part from accidentally "
          "containing, say, almost no Obesity-type-III records.")
p.font.size = Pt(12)
p.font.color.rgb = DARK
p.font.name = FONT
footer(s, 2)

# ============================== 3. Column dictionary ==============================
s = slide("2. What every column means", "The dataset uses many short codes — here is the full dictionary")
left = [["Code", "Full meaning", "Values"],
        ["Gender", "Biological sex of the respondent", "Male / Female"],
        ["Age", "Age in years", "14 – 61"],
        ["Height", "Height in metres", "1.45 – 1.98"],
        ["Weight", "Weight in kilograms", "39 – 165"],
        ["family_history", "Whether a family member has been overweight", "0 = no, 1 = yes"],
        ["FAVC", "Frequent consumption of high-caloric food", "0 = no, 1 = yes"],
        ["FCVC", "Frequency of consumption of vegetables", "1 = low … 3 = high"],
        ["NCP", "Number of main meals per day", "1 – 4"],
        ["CAEC", "Consumption of food between meals", "no / Sometimes / Frequently / Always"]]
right = [["Code", "Full meaning", "Values"],
         ["CH2O", "Daily water intake", "1 = low … 3 = high"],
         ["SCC", "Self-monitoring of calorie consumption", "0 = no, 1 = yes"],
         ["FAF", "Physical-activity frequency (days per week)", "0 – 3"],
         ["TUE", "Time spent using electronic devices (hours per day)", "0 – 2"],
         ["CALC", "Consumption of alcohol", "no / Sometimes / Frequently"],
         ["SMOKE", "Whether the person smokes", "0 = no, 1 = yes"],
         ["MTRANS", "Main mode of transportation", "Walking / Bike / Motorbike / Public transport / Car"],
         ["id", "Row identifier — removed before training", "0 – 20,757"],
         ["NObeyesdad", "Obesity level — this is the target we predict", "7 classes"]]
table(s, left, 0.45, 1.4, 6.1, 4.9, col_w=[1.15, 3.4, 1.55], size=10)
table(s, right, 6.8, 1.4, 6.1, 4.9, col_w=[1.15, 3.4, 1.55], size=10)
text(s, "Note: in CAEC and CALC the symbol “0” is the dataset’s way of writing “no”, "
        "not the number zero — one of the defects we had to repair (see slide 4).",
     0.45, 6.5, 12.4, 0.7, size=11.5, color=ACCENT)
footer(s, 3)

# ============================== 4. Data quality ==============================
s = slide("3. Data-quality checks and defects found",
          "The file looked clean — but three hidden problems would have corrupted the labels")
bullets(s, [
    ("Checks we ran: ", "missing values per column, duplicate rows, numeric ranges "
                        "(no negative ages or heights), and class balance. All clean."),
    ("Defect 1 — corrupted column name: ", "the target column arrived as “0be1dad”; the letter "
                                           "“N” had been replaced by the digit “0”. Renamed to NObeyesdad."),
    ("Defect 2 — corrupted label: ", "one class was written “0rmal_Weight” instead of “Normal_Weight”. "
                                     "Left unfixed, this would have created a phantom 8th class."),
    ("Defect 3 — ambiguous coding: ", "in CAEC and CALC the value “0” means “no”. If it were read as a "
                                      "number it would be silently sorted between other categories."),
    ("Structural finding: ", "the average BMI (Body Mass Index = weight in kilograms ÷ height in metres squared) "
                             "rises monotonically across the seven classes — 17.6, 22.0, 26.1, 28.2, 32.2, 36.5, 41.8."),
    ("Why that matters: ", "the labels are effectively defined by BMI, so height and weight are near-shortcut "
                           "features. This is exactly why we run two feature-set experiments (next slide)."),
], 0.6, 1.45, 12.2, 4.6, size=13, gap=12)
footer(s, 4)

# ============================== 5. Task definition ==============================
s = slide("4. Task definition and the two feature sets",
          "What we predict, and why we deliberately train two versions of every model")
bullets(s, [
    ("Primary task — binary classification: ", "Obesity (types I, II, III) versus non-obesity "
                                               "(insufficient weight, normal weight, overweight levels I and II)."),
    ("Optional extension — multi-class classification: ", "all seven obesity levels kept as separate classes."),
], 0.6, 1.45, 12.2, 1.2, size=13.5, gap=10)

table(s, [["Feature set", "What goes in", "Why we run it"],
          ["Lifestyle-only",
           "gender, age, family history, and all 11 lifestyle variables "
           "(FAVC, FCVC, NCP, CAEC, CH2O, SCC, FAF, TUE, CALC, SMOKE, MTRANS). "
           "Height, weight and BMI are excluded.",
           "Tests whether a questionnaire alone carries enough signal — "
           "this is the model whose results can actually be interpreted."],
          ["Measurement-inclusive",
           "the same 14 features plus height, weight and the derived BMI.",
           "A comparison only. It scores higher, but permutation tests show it is "
           "essentially reading BMI, so we never present it as the main result."]],
      0.6, 2.85, 12.15, 2.5, col_w=[2.3, 4.6, 5.25], size=11.5)

text(s, "Honest framing: the dataset records a person’s current status, not a future outcome. "
        "Our tool is therefore a screening aid, not a medical diagnosis nor a prediction of future risk.",
     0.6, 5.75, 12.15, 0.8, size=12.5, color=ACCENT)
footer(s, 5)

# ============================== 6. Protocol ==============================
s = slide("5. Experimental protocol",
          "How we make sure the test score is trustworthy")
bullets(s, [
    ("Stratified split: ", "70 % training / 15 % validation / 15 % test, stratified on the seven-class "
                           "label, random seed fixed at 42 so the split is identical on every run."),
    ("Preprocessing fitted on training data only: ", "scaling of numeric columns and One-Hot Encoding "
                                                     "(OHE = turning each category into its own 0/1 column) are wrapped inside a scikit-learn "
                                                     "Pipeline, so statistics are never computed from validation or test rows."),
    ("Validation set is for decisions: ", "we use it to select hyper-parameters (the settings of a model "
                                          "that are chosen by us, not learned from data) and the decision threshold."),
    ("Test set is touched exactly once: ", "a separate script, evaluate.py, reads it at the very end. "
                                           "The training script train.py physically never opens the test file."),
    ("Threshold tuning: ", "we scanned 91 candidate thresholds from 0.05 to 0.95 on the validation set and "
                           "kept the one maximising the F1 score (0.50 for the lifestyle model, 0.54 for the other)."),
], 0.6, 1.45, 12.2, 4.5, size=13, gap=13)
footer(s, 6)

# ============================== 7. Models ==============================
s = slide("6. Models we trained", "Three models, fully implemented by us with scikit-learn on our own data")
bullets(s, [
    ("1. Majority-class baseline (Dummy Classifier): ", "always predicts the most frequent class. "
                                                        "It carries no information — it exists to define the floor that a real model must beat."),
    ("2. Logistic Regression (LR): ", "a linear model that learns one weight per feature and outputs a "
                                      "probability between 0 and 1. We tried 6 configurations: regularisation strength "
                                      "C (the penalty for large weights) ∈ {0.1, 1, 10}, with and without class weighting."),
    ("3. Random Forest (RF) — our main model: ", "an ensemble of 400 decision trees. Each tree is grown on a "
                                                 "bootstrap resample (sampling 14,530 records with replacement, so each tree sees a slightly "
                                                 "different dataset) and at every split it may only consider √p ≈ 5 randomly offered features. "
                                                 "The 400 trees then vote, and the fraction voting “obesity” is the predicted probability. "
                                                 "We tried 8 configurations (tree depth, minimum samples per leaf, class weighting)."),
    ("Total: ", "2 feature sets × 15 configurations = 30 fitted pipelines, 24 seconds in total on an ordinary "
                "laptop CPU (Central Processing Unit) — no graphics card needed."),
], 0.6, 1.45, 12.2, 4.6, size=13, gap=13)
footer(s, 7)

# ============================== 8. Binary results ==============================
s = slide("7. Results on the held-out test set", "Binary task: obesity (types I–III) versus non-obesity")
table(s, [["Feature set", "Model", "Accuracy", "Precision", "Recall", "F1 score", "ROC-AUC", "PR-AUC"],
          ["Lifestyle-only", "Majority baseline", "0.508", "0.000", "0.000", "0.000", "0.500", "0.492"],
          ["Lifestyle-only", "Logistic Regression", "0.802", "0.730", "0.946", "0.824", "0.902", "0.880"],
          ["Lifestyle-only", "Random Forest  ◄ main", "0.897", "0.904", "0.884", "0.894", "0.964", "0.967"],
          ["Measurement-inclusive", "Logistic Regression", "0.968", "0.969", "0.965", "0.967", "0.994", "0.995"],
          ["Measurement-inclusive", "Random Forest", "0.977", "0.982", "0.971", "0.976", "0.996", "0.997"]],
      0.5, 1.4, 12.35, 2.0, col_w=[2.5, 2.5, 1.15, 1.15, 1.05, 1.05, 1.05, 1.05], size=11.5)

text(s, "What the metrics mean:", 0.5, 4.05, 12.3, 0.35, size=12.5, bold=True, color=BLUE)
bullets(s, [
    ("Precision — ", "of all the people the model flags as obese, the share who truly are."),
    ("Recall — ", "of all the truly obese people, the share the model manages to catch."),
    ("F1 score — ", "the harmonic mean of precision and recall; a single number that penalises "
                    "models which sacrifice one for the other."),
    ("ROC-AUC — ", "Receiver Operating Characteristic, Area Under the Curve: the probability the model "
                   "ranks a random obese person above a random non-obese one. 0.5 equals coin-flipping."),
    ("PR-AUC — ", "Precision-Recall Area Under the Curve; focuses on the positive (obesity) class and is "
                  "more informative than ROC-AUC when classes are imbalanced."),
], 0.5, 4.5, 12.3, 2.4, size=11.5, gap=6)
footer(s, 8)

# ============================== 9. Multiclass + confusion ==============================
s = slide("8. Seven-class extension and error pattern",
          "Lifestyle model: 72.7 % accuracy ·  Measurement model: 90.0 % accuracy")
if (FIG / "cm_lifestyle_rf.png").exists():
    s.shapes.add_picture(str(FIG / "cm_lifestyle_rf.png"), Inches(0.75), Inches(1.55), height=Inches(4.3))
bullets(s, [
    ("Reading the matrix: ", "rows are the true condition, columns are what the model predicted."),
    ("Correct calls: ", "1,439 non-obese and 1,353 obese people classified correctly."),
    ("Mistakes: ", "144 non-obese people wrongly flagged (false alarms) and 178 obese people missed."),
    ("Why we report this: ", "accuracy alone hides these two very different kinds of error. In a "
                             "screening tool, a missed case and a false alarm have different costs, so both must be visible."),
    ("Seven-class result: ", "identifying the exact level is much harder than the binary question — "
                             "the lifestyle model is right 72.7 % of the time, which is still far above the "
                             "14.3 % a random guess would achieve across seven classes."),
], 6.6, 1.75, 6.2, 4.6, size=12.5, gap=11)
footer(s, 9)

# ============================== 10. Interpretation ==============================
s = slide("9. What the models actually rely on",
          "Permutation importance: shuffle one feature, measure how much accuracy drops")
if (FIG / "perm_lifestyle.png").exists():
    s.shapes.add_picture(str(FIG / "perm_lifestyle.png"), Inches(0.5), Inches(1.5), width=Inches(6.1))
if (FIG / "perm_measurement.png").exists():
    s.shapes.add_picture(str(FIG / "perm_measurement.png"), Inches(6.8), Inches(1.5), width=Inches(6.1))
text(s, "Lifestyle-only model  (the one worth interpreting)", 0.5, 6.0, 6.1, 0.35,
     size=11.5, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
text(s, "Measurement-inclusive model  (comparison only)", 6.8, 6.0, 6.1, 0.35,
     size=11.5, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
text(s, "Key finding: BMI (0.153) and weight (0.131) dominate the measurement model, while the "
        "next feature — family history, 0.005 — is about thirty times weaker. The lifestyle model instead "
        "leans on age, family history, snacking between meals, vegetable intake and high-calorie food. "
        "These are associations, not causes.",
     0.5, 6.42, 11.5, 0.8, size=12, color=DARK)
footer(s, 10)

# ============================== 11. Evidence ==============================
s = slide("10. Evidence of completed work", "Everything below is finished and reproducible from the repository")
bullets(s, [
    ("1. Reproducible pipeline (three scripts, run in order): ", "prepare_data.py (clean, repair labels, "
                                                                 "split) → train.py (fit on training data, tune on validation only) → evaluate.py "
                                                                 "(read the test set once, produce every number and figure in this deck)."),
    ("2. Saved artefacts: ", "trained pipelines with their preprocessing embedded, three metric files in "
                             "JSON (JavaScript Object Notation) format, and seven figures (curves, confusion matrices, importance plots)."),
    ("3. Interactive demo: ", "a questionnaire web page at http://localhost:8501. It shows both models "
                              "side by side, displays the seven-class probability bars, and can draw a real held-out "
                              "record to show whether the prediction matches the true label."),
    ("4. Version control: ", "a local Git repository is initialised with 25 tracked files and one commit; "
                             "large model binaries are excluded and can be rebuilt in under 30 seconds."),
], 0.6, 1.45, 12.2, 3.9, size=13, gap=13)
footer(s, 11)

# ============================== 12. Problems ==============================
s = slide("11. Problems we encountered", "Four real obstacles — and what we did about each one")
bullets(s, [
    ("Silent type-mismatch bug (the most dangerous one): ", "the four yes/no columns are integers "
                                                            "in the file, but a web form always submits text. Passing “1” as text made the One-Hot "
                                                            "Encoder treat it as an unseen category and encode it as all zeros — no error, no warning. "
                                                            "On the same record the probability collapsed from 0.978 to 0.486. We found it by "
                                                            "deliberately testing both types, and fixed it with explicit integer conversion."),
    ("Corrupted labels in the raw file: ", "a misspelt column name and a misspelt class. Fixed by explicit "
                                           "renaming during cleaning; without this, a phantom eighth class would have appeared."),
    ("Out-of-distribution inputs: ", "our first hand-made demo profile pushed every slider to an extreme "
                                     "and received only 25 % obesity probability despite a BMI of 38.5, because that combination does not "
                                     "exist in the training data. We now use two real records from the dataset as demo presets."),
    ("Tooling: ", "the Streamlit demo library would not finish installing on our network, so we built the "
                  "demo directly on the Python standard library’s HTTP server — zero extra dependencies, and it starts in about four seconds."),
], 0.6, 1.45, 12.2, 4.9, size=12.5, gap=13)
footer(s, 12)

# ============================== 13. Next steps ==============================
s = slide("12. Next steps", "What we will do between now and the final submission")
bullets(s, [
    ("Push the repository to GitHub ", "and share the link; add Git LFS (Large File Storage) if we decide "
                                       "to version the model binaries as well."),
    ("Fairness and subgroup analysis: ", "check whether accuracy, false-alarm rate and miss rate differ "
                                         "between men and women and across age bands — a screening tool should behave equally well for everyone."),
    ("Per-prediction explanations with SHAP ", "(SHapley Additive exPlanations): show which features pushed "
                                               "one particular person’s prediction up or down, instead of only global importance."),
    ("Probability calibration: ", "verify that “70 % probability” really corresponds to 7 correct cases "
                                  "in 10, and apply calibration if it does not."),
    ("Cross-validation: ", "repeat the split several times and report the spread, so a single lucky split "
                           "cannot flatter our numbers."),
    ("Final deliverables: ", "the written report, the slide deck, and a rehearsal of the five-minute presentation."),
], 0.6, 1.45, 12.2, 4.6, size=13, gap=13)
footer(s, 13)

# ============================== 14. Closing ==============================
s = prs.slides.add_slide(BLANK)
band = s.shapes.add_shape(1, 0, Inches(2.6), W, Inches(2.3))
band.fill.solid()
band.fill.fore_color.rgb = BLUE
band.line.fill.background()
band.shadow.inherit = False
tf = band.text_frame
tf.vertical_anchor = MSO_ANCHOR.MIDDLE
tf.margin_left = Inches(0.8)
p = tf.paragraphs[0]
p.text = "Summary"
p.font.size = Pt(30)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = FONT
p2 = tf.add_paragraph()
p2.text = ("Clean, verified data  →  leakage-free protocol  →  three models, two feature sets  →  "
           "test set used once  →  results we can defend")
p2.font.size = Pt(15)
p2.font.color.rgb = RGBColor(0xCF, 0xE2, 0xF5)
p2.font.name = FONT
bullets(s, [
    ("Headline number: ", "without using height, weight or BMI at all, our Random Forest reaches "
                          "an F1 score of 0.894 and a ROC-AUC of 0.964 on data it has never seen."),
    ("Headline caveat: ", "the stronger measurement model is mostly reading BMI — which is precisely "
                          "why we report both rather than only the flattering one."),
], 0.85, 5.2, 11.6, 1.6, size=14, gap=12)

OUT.parent.mkdir(parents=True, exist_ok=True)
prs.save(str(OUT))
print(f"已生成: {OUT}")
print(f"共 {len(prs.slides.__iter__.__self__._sldIdLst)} 页")
