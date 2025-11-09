# firebase_worker.py
import time, json, joblib, numpy as np
from pathlib import Path
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db

# ==== CONFIG ====
DEVICE_PATH = "/devices/esp32_1"
IMU_NODE    = DEVICE_PATH + "/imu"
AI_NODE     = DEVICE_PATH + "/ai"
EVENTS_NODE = DEVICE_PATH + "/events"

MODEL_DIR = Path("backend/model")
FEATURE_ORDER = json.load(open(MODEL_DIR/'feature_order.json'))
clf    = joblib.load(MODEL_DIR/'trained_model.pkl')
scaler = joblib.load(MODEL_DIR/'scaler.pkl')

# ==== Firebase Admin SDK setup ====
# 1) In Firebase console -> Service Accounts -> Generate new private key
# 2) Save it as serviceAccountKey.json beside this script
cred = credentials.Certificate("mpu6050-data-24546-firebase-adminsdk-fbsvc-1570270ddf.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://mpu6050-data-24546-default-rtdb.firebaseio.com/"
})

def engineer(imu):
    # imu dict expected: ax,ay,az,gx,gy,gz (float)
    ax, ay, az = float(imu.get('ax',0)), float(imu.get('ay',0)), float(imu.get('az',0))
    gx, gy, gz = float(imu.get('gx',0)), float(imu.get('gy',0)), float(imu.get('gz',0))
    amp10x = (ax*ax + ay*ay + az*az) ** 0.5 * 10.0
    gvec   = (gx*gx + gy*gy + gz*gz) ** 0.5
    # For gz_spike we need history; approximate with 1-step diff if old gz available in AI node
    try:
        prev = db.reference(AI_NODE + "/last_gz").get() or 0.0
    except:
        prev = 0.0
    gz_spike = abs(gz - float(prev))
    db.reference(AI_NODE + "/last_gz").set(gz)  # store for next time

    feats = {
        'amp10x': amp10x,
        'gvec': gvec,
        'az': az, 'ax': ax, 'ay': ay,
        'gz_spike': gz_spike,
        'gx': gx, 'gy': gy, 'gz': gz
    }
    # order into array
    x = np.array([[feats[k] for k in FEATURE_ORDER]], dtype=float)
    xs = scaler.transform(x)
    return xs, feats

def write_prediction(pred, proba, feats):
    payload = {
        "features": feats,
        "prediction": int(pred),       # 1=fall, 0=non-fall
        "prob_fall": float(proba),
        "ts_iso": datetime.utcnow().isoformat() + "Z"
    }
    db.reference(AI_NODE).set(payload)
    # optional: push event if strong fall
    if pred == 1 and proba >= 0.80:
        db.reference(EVENTS_NODE).push({
            "type": "ai_fall_detected",
            "prob": float(proba),
            "ts_ms": int(time.time()*1000)
        })

def on_change(event):
    # event.data is full IMU object
    imu = event.data
    if not isinstance(imu, dict): return
    try:
        xs, feats = engineer(imu)
        proba = clf.predict_proba(xs)[0,1]
        pred  = int(proba >= 0.65)  # threshold; tune later
        write_prediction(pred, proba, feats)
        print("AI:", pred, f"(p={proba:.2f})", "features:", feats)
    except Exception as e:
        print("Error:", e)

def main():
    ref = db.reference(IMU_NODE)
    # initial fetch to avoid None
    cur = ref.get()
    # attach stream listener
    ref.listen(lambda ev: on_change(ev))

if __name__ == "__main__":
    main()
