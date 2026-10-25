"""
交互式预测服务（零额外依赖，只用标准库 + 已有的 pandas/sklearn/joblib）
启动: python -X utf8 predict_server.py
访问: http://localhost:8501
"""
import json
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
MODEL_DIR = ROOT / "outputs" / "models"
SPLIT_DIR = ROOT / "data" / "split"
PORT = 8501

print("正在加载模型 ...")
MODELS = {}
for key in ["lifestyle__rf", "measurement__rf",
            "lifestyle__multiclass", "measurement__multiclass"]:
    MODELS[key] = joblib.load(MODEL_DIR / f"{key}.joblib")
    print(f"  loaded: {key}")

TEST = pd.read_csv(SPLIT_DIR / "test.csv")
SAMPLE_COLS = ["Gender", "Age", "Height", "Weight", "family_history_with_overweight",
               "FAVC", "FCVC", "NCP", "CAEC", "SMOKE", "CH2O", "SCC", "FAF",
               "TUE", "CALC", "MTRANS"]
print("模型加载完毕\n")


def to_float(v):
    return float(v)


# 这四列在数据集中是 0/1 整数。若传成字符串，OneHotEncoder 会当成未知类别
# 静默编码成全 0，预测结果会完全错误（实测 0.978 -> 0.486），必须显式转 int。
FLAG_COLS = ["family_history_with_overweight", "FAVC", "SMOKE", "SCC"]


def predict(payload):
    row = {k: payload[k] for k in SAMPLE_COLS}
    for c in ["Age", "Height", "Weight", "FCVC", "NCP", "CH2O", "FAF", "TUE"]:
        row[c] = to_float(row[c])
    for c in FLAG_COLS:
        row[c] = int(str(row[c]))
    row["BMI"] = row["Weight"] / (row["Height"] ** 2)
    df = pd.DataFrame([row])

    result = {"bmi": round(row["BMI"], 1)}
    for fs in ["lifestyle", "measurement"]:
        b = MODELS[f"{fs}__rf"]
        prob = float(b["pipeline"].predict_proba(df[b["feature_cols"]])[0][1])
        mb = MODELS[f"{fs}__multiclass"]
        mc_proba = mb["pipeline"].predict_proba(df[mb["feature_cols"]])[0]
        pairs = sorted([{"cls": c, "prob": round(float(v), 4)}
                        for c, v in zip(mb["pipeline"].classes_.tolist(), mc_proba)],
                       key=lambda x: -x["prob"])
        result[fs] = {
            "obesity_prob": round(prob, 4),
            "threshold": b["threshold"],
            "is_obese": bool(prob >= b["threshold"]),
            "level": pairs[0]["cls"],
            "level_prob": pairs[0]["prob"],
            "multiclass": pairs,
        }
    return result


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8",
                       (WEB_DIR / "index.html").read_bytes())
        elif path == "/api/sample":
            target = parse_qs(urlparse(self.path).query).get("target", [None])[0]
            pool = TEST if target is None else TEST[TEST.NObeyesdad == target]
            r = pool.sample(1, random_state=random.randint(0, 10 ** 6)).iloc[0]
            payload = {}
            for c in SAMPLE_COLS:
                v = r[c]
                if c in FLAG_COLS:
                    payload[c] = str(int(v))
                elif isinstance(v, str):
                    payload[c] = v
                else:
                    payload[c] = round(float(v), 3)
            body = json.dumps({"input": payload, "truth": str(r["NObeyesdad"])},
                              ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)
        else:
            self._send(404, "text/plain; charset=utf-8", b"404 Not Found")

    def do_POST(self):
        if urlparse(self.path).path != "/api/predict":
            self._send(404, "text/plain; charset=utf-8", b"404 Not Found")
            return
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        out = predict(payload)
        self._send(200, "application/json; charset=utf-8",
                   json.dumps(out, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"服务已启动 -> http://localhost:{PORT}")
    print("按 Ctrl+C 停止")
    server.serve_forever()
