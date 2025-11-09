import os
import json
from flask import Flask, request, jsonify, send_from_directory, render_template
import numpy as np
import joblib

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(APP_ROOT, "model", "trained_model.pkl"))
with open(os.path.join(APP_ROOT, "model", "feature_order.json"), "r") as f:
    FEATURE_ORDER = json.load(f)

app = Flask(__name__, static_folder="static", template_folder="templates")

@app.get("/")
def home():
    # Serve the dashboard HTML (pure front-end talks to Firebase or to /predict)
    return render_template("index.html")

@app.get("/health")
def health():
    return {"ok": True}

def _features_from_payload(d: dict):
    ax = float(d.get("ax", 0.0))
    ay = float(d.get("ay", 0.0))
    az = float(d.get("az", 0.0))
    gx = float(d.get("gx", 0.0))
    gy = float(d.get("gy", 0.0))
    gz = float(d.get("gz", 0.0))
    amp10x = float(d.get("amp10x", np.sqrt(ax*ax+ay*ay+az*az)*10.0))
    gvec = float(np.sqrt(gx*gx + gy*gy + gz*gz))
    gz_spike = abs(float(d.get("gz_prev", 0.0)) - gz)
    feats_map = {
        "amp10x": amp10x, "gvec": gvec, "az": az, "ax": ax, "ay": ay,
        "gz_spike": gz_spike, "gx": gx, "gy": gy, "gz": gz
    }
    return np.array([feats_map[k] for k in FEATURE_ORDER], dtype=float)

@app.post("/predict")
def predict():
    d = request.get_json(force=True, silent=True) or {}
    X = _features_from_payload(d).reshape(1, -1)
    prob = float(model.predict_proba(X)[0,1])
    is_fall = bool(prob >= 0.5)
    return jsonify({"prob_fall": round(prob, 4), "is_fall": is_fall})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
