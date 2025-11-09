# AIoT Fall Detector (Python + ML, No Node.js)

Generated: 2025-11-09T08:17:27.588906

## Structure
```
backend/
  app.py                  # Flask server (serves frontend + /predict API)
  firebase_listener.py    # Optional: listen to Firebase RTDB and run ML
  alerts.py               # Optional: Twilio SMS/WhatsApp/Call helpers
  requirements.txt
  model/
    trained_model.pkl     # Trained GradientBoostingClassifier
    feature_order.json
    TRAINING_REPORT.txt
frontend/ (served from templates/index.html via Flask)
```

## Quick Start
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open: http://localhost:8000

Click **Simulate Sample** to test end-to-end prediction and chart updates.

## Use with Firebase (optional)
1. Download a Firebase Service Account JSON -> save as `backend/serviceAccountKey.json`
2. Set env var:
   - `FIREBASE_DB_URL=https://<your-project>.firebaseio.com`
3. Run listener:
```bash
cd backend
python firebase_listener.py
```

This listens to `/devices/esp32_1/imu` and updates `/fallState` and `/events` using the ML model.

## Twilio Alerts (optional)
Set environment variables:
```
TWILIO_SID=ACxxxxxxxxxxxx
TWILIO_AUTH=xxxxxxxxxxxxxx
TWILIO_SMS_NUMBER=+1xxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+1xxxxxxxxx
EMERGENCY_PHONE=+91xxxxxxxxxx
```
Then import and use functions in `alerts.py` (e.g., from firebase_listener).

## Re-training
You can retrain by editing and running a new `train.py` (optional) using your dataset with columns:
[ax, ay, az, gx, gy, gz, amp10x]. For now, this bundle includes a model trained on synthetic but realistic patterns.
