import os, json, time, datetime
import numpy as np
import pickle
from threading import Event
from firebase_admin import credentials, db, initialize_app

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(APP_ROOT, "model", "trained_model.pkl"), "rb") as f:
    model = pickle.load(f)
with open(os.path.join(APP_ROOT, "model", "feature_order.json"), "r") as f:
    FEATURE_ORDER = json.load(f)

def features_from_imu(d: dict, prev_gz: float = 0.0):
    ax = float(d.get("ax", 0.0))
    ay = float(d.get("ay", 0.0))
    az = float(d.get("az", 0.0))
    gx = float(d.get("gx", 0.0))
    gy = float(d.get("gy", 0.0))
    gz = float(d.get("gz", 0.0))
    amp10x = float(d.get("amp10x", np.sqrt(ax*ax+ay*ay+az*az)*10.0))
    gvec = float(np.sqrt(gx*gx + gy*gy + gz*gz))
    gz_spike = abs(prev_gz - gz)
    feats = {"amp10x": amp10x, "gvec": gvec, "az": az, "ax": ax, "ay": ay, "gz_spike": gz_spike, "gx": gx, "gy": gy, "gz": gz}
    return np.array([feats[k] for k in FEATURE_ORDER], dtype=float), gz

def main():
    # Hardcoded Firebase configuration
    sa_path = "mpu6050-data-24546-firebase-adminsdk-fbsvc-1570270ddf.json"
    db_url = "https://mpu6050-data-24546-default-rtdb.firebaseio.com"
    
    if not os.path.exists(sa_path):
        print(f"Error: Service account file not found at {sa_path}")
        return
        
    try:
        cred = credentials.Certificate(sa_path)
        initialize_app(cred, {"databaseURL": db_url})
        print("Successfully connected to Firebase")
    except Exception as e:
        print(f"Failed to initialize Firebase: {str(e)}")
        return

    device_path = "/devices/esp32_1"
    imu_ref = db.reference(device_path + "/imu")
    fall_ref = db.reference(device_path + "/fallState")
    events_ref = db.reference(device_path + "/events")

    stop = Event()
    prev_gz = 0.0
    last_ts = 0

    print("Listening for IMU updates...")
    def handler(event):
        nonlocal prev_gz, last_ts
        if event.path not in ["/", ""] and not isinstance(event.data, dict):
            # Not a full object; we will refetch full imu
            imu = imu_ref.get() or {}
        else:
            imu = event.data or {}
        if not imu:
            return
        ts = int(imu.get("timestamp_ms", 0))
        if ts and ts == last_ts:
            return
        X, prev_gz = features_from_imu(imu, prev_gz)
        prob = float(model.predict_proba(X.reshape(1,-1))[0,1])
        is_fall = prob >= 0.5
        # Update nodes
        fall_ref.set(bool(is_fall))
        if is_fall:
            ev = {"type": "fall_detected", "message": "⚠️ Fall Detected (ML)", "timestamp_ms": int(time.time()*1000), "prob": prob}
            events_ref.push(ev)
        last_ts = ts

    imu_ref.listen(handler)
    try:
        while not stop.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()

if __name__ == "__main__":
    main()
