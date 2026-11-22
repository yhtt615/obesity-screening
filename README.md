# Lifestyle-Based Obesity Screening with Lightweight Machine Learning

Course project — 吴炳言 / 杨皓童 / 杜沛霖

**Task.** Classify a person's *current* obesity status (binary: Obesity I–III vs
non-obesity; optional 7-class extension) from lifestyle + demographic features.
This is a **screening tool, not a medical diagnosis or future-risk prediction**.

**Data.** `data/obesity_level.csv` — 20,758 rows × 18 columns, no missing values,
no duplicates. Kaggle Obesity Risk Dataset (distributed via Heywhale).
Note: the raw target column is misspelled (`0be1dad` → renamed to `NObeyesdad`,
`0rmal_Weight` → `Normal_Weight`); `0` in `CAEC`/`CALC` means "no".

## How to run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python src/prepare_data.py   # clean, label, stratified 70/15/15 split
python src/train.py          # fit on train, tune on validation ONLY
python src/evaluate.py       # touch the test set ONCE, plots + permutation importance

python -X utf8 predict_server.py   # interactive web UI -> http://localhost:8501
streamlit run app.py               # alternative Streamlit demo
```

## ⚠️ Gotcha: 0/1 flag columns must stay integers

`family_history_with_overweight`, `FAVC`, `SMOKE`, `SCC` are stored as **int64 0/1**
in the CSV. In the training `Pipeline` they go through `OneHotEncoder`. If you pass
them as **strings** at inference time (`"1"` instead of `1`), the encoder silently
treats them as unknown categories and encodes them as **all zeros** — no error, no
warning, just wrong predictions.

Measured on a real Obesity_Type_III record: `1` → 0.978 vs `"1"` → 0.486.

Web forms always submit strings, so **both** `predict_server.py` and `app.py`
explicitly cast these four columns back to `int` before building the DataFrame.
If you write your own inference code, do the same.

## Deliverables for the course

```bash
python tools/make_report.py   # one-page progress report  -> outputs/Second_Progress_Report.docx
python tools/make_slides.py   # 14-slide deck             -> outputs/Second_Progress_Report.pptx
```

`PROGRESS_REPORT_2.md` is the plain-text source of the report if you prefer to
paste it into a submission system.

### Publishing to GitHub

The local Git repository is already initialised with one commit and 25 tracked
files (model binaries are excluded — see `.gitignore`). Create an empty
repository on GitHub, then:

```bash
git remote add origin https://github.com/<your-account>/obesity-screening.git
git branch -M main
git push -u origin main
```

The repository URL used in the reports and slides is
`https://github.com/yhtt615/obesity-screening`.

## Design decisions

- **Two feature sets.** `lifestyle` excludes Height/Weight/BMI;
  `measurement` includes them. Labels are BMI-derived, so the measurement
  model is a near-shortcut — the comparison quantifies how much predictions
  rely on body measurements (see results below).
- **Leakage prevention.** All preprocessing (imputation, encoding, scaling) is
  fitted inside a scikit-learn `Pipeline` on the training fold only.
  Validation is used for hyperparameters and the decision threshold;
  the test set is read exactly once, by `evaluate.py`.
- **Split.** Stratified 70 / 15 / 15 by the 7-class label, seed = 42.

## Test-set results (binary task)

| Feature set | Model | Accuracy | Precision (obesity) | Recall (obesity) | F1 (obesity) | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| Lifestyle-only | Majority baseline | 0.508 | 0.000 | 0.000 | 0.000 | 0.500 | 0.492 |
| Lifestyle-only | Logistic Regression | 0.802 | 0.730 | 0.946 | 0.824 | 0.902 | 0.880 |
| Lifestyle-only | **Random Forest** | **0.897** | 0.904 | 0.884 | **0.894** | **0.964** | **0.967** |
| Measurement-inclusive | Logistic Regression | 0.968 | 0.969 | 0.965 | 0.967 | 0.994 | 0.995 |
| Measurement-inclusive | **Random Forest** | **0.977** | 0.982 | 0.971 | **0.976** | **0.996** | **0.997** |

7-class extension (Random Forest, test accuracy): lifestyle **0.727**, measurement **0.900**.

## Key interpretation (permutation importance, test set)

- **Lifestyle-only model:** strongest signals are **Age, family history,
  snacking between meals (CAEC), vegetable intake (FCVC), high-calorie food
  (FAVC)**. Smoking and calorie-intake monitoring contribute ≈ 0.
- **Measurement-inclusive model:** BMI (0.153) and Weight (0.131) dominate;
  the next feature (family history, 0.005) is ~30× weaker — i.e. the
  measurement model is essentially reading BMI. This is why both models are
  reported, and why lifestyle results are the meaningful ones to interpret.

All importance figures describe **predictive association, not causation**.

## Limitations

- Labels are derived from BMI buckets of (possibly synthetic) records, so
  "obesity" here means a BMI category, not a clinical assessment.
- Dataset is synthetic-augmented (20k+ rows); lifestyle effect sizes may not
  transfer to real populations.
- No fairness analysis across gender/age subgroups yet (future work).

## Repository layout

```
data/                 raw + cleaned CSV, stratified splits (data/split/)
src/prepare_data.py   step 1 — clean, rename/fix labels, split
src/train.py          step 2 — fit + validation tuning (never reads test)
src/evaluate.py       step 3 — single test-set evaluation, plots, importance
app.py                step 4 — Streamlit questionnaire demo
outputs/models/       trained pipelines (.joblib, compressed)
outputs/figures/      ROC/PR curves, confusion matrices, importance plots
outputs/metrics/      data_report.json, val_results.json, test_results.json
```
