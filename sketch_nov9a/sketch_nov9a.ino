/***************************************************
   ESP32 + MPU6050 + Blynk + Firebase
   ✅ Updated Version with Improved Fall Logic
****************************************************/

// ✅ Choose ONE Blynk Template
#define BLYNK_TEMPLATE_ID           "TMPL3c1f-hKo4"
#define BLYNK_TEMPLATE_NAME         "AIoT Fall Detector"
#define BLYNK_AUTH_TOKEN            "srY98glJSfxfm1uOtI-JIkyzgYsnfdxu"

#define BLYNK_TEMPLATE_ID           "TMPL3znMbJVg7"
#define BLYNK_TEMPLATE_NAME         "Quickstart Device"
#define BLYNK_AUTH_TOKEN            "ImoZIlmO0gzchju1C5oBdclrRcrjEuS2"

#define BLYNK_PRINT Serial

#include <Wire.h>
#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <FirebaseESP32.h>

// ===== FIREBASE CONFIG =====
#define API_KEY      "AIzaSyAXv119W8eN7PiJ1h13QUw3VPjqlnbvCTE"
#define DATABASE_URL "https://mpu6050-data-24546-default-rtdb.firebaseio.com/"

// ===== WIFI CONFIG =====
const char* ssid = "Jay";
const char* pass = "12345678";

// Firebase 
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

String DEVICE_PATH = "/devices/esp32_1";

// ---- MPU6050 ----
const int MPU_addr = 0x68;
int16_t AcX, AcY, AcZ, Tmp, GyX, GyY, GyZ;
float ax, ay, az, gx, gy, gz;

// ---- Fall Detection Variables ----
boolean fall = false;
boolean trigger1 = false;
boolean trigger2 = false;
boolean trigger3 = false;

byte trigger1count = 0;
byte trigger2count = 0;
byte trigger3count = 0;

int angleChange = 0;

BlynkTimer timer;

/*************** READ MPU6050 ****************/
void mpu_read() {
  Wire.beginTransmission(MPU_addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_addr, 14, true);

  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Tmp = Wire.read() << 8 | Wire.read();
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();

  ax = (AcX - 2050) / 16384.00;
  ay = (AcY - 77) / 16384.00;
  az = (AcZ - 1947) / 16384.00;

  gx = (GyX + 270) / 131.07;
  gy = (GyY - 351) / 131.07;
  gz = (GyZ + 136) / 131.07;
}

/*************** SEND IMU + Fall Status to Firebase ****************/
void sendIMUToFirebase() {
  if (!Firebase.ready()) return;

  float Raw_Amp = sqrt(ax * ax + ay * ay + az * az);
  int Amp = Raw_Amp * 10;

  FirebaseJson json;
  json.set("ax", ax);
  json.set("ay", ay);
  json.set("az", az);
  json.set("gx", gx);
  json.set("gy", gy);
  json.set("gz", gz);
  json.set("amp10x", Amp);
  json.set("isFall", fall);
  json.set("timestamp_ms", millis());

  Firebase.setJSON(fbdo, DEVICE_PATH + "/imu", json);
  Firebase.setBool(fbdo, DEVICE_PATH + "/fallState", fall);
}

/*************** LOG FALL EVENT IN FIREBASE ****************/
void pushFallEvent() {
  FirebaseJson event;
  event.set("type", "fall_detected");
  event.set("message", "⚠️ Fall Detected!");
  event.set("timestamp_ms", millis());

  Firebase.pushJSON(fbdo, DEVICE_PATH + "/events", event);
  Serial.println("✅ Fall Event Logged");
}

/*************** FIREBASE SETUP ****************/
void setupFirebase() {
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;

  Firebase.signUp(&config, &auth, "", "");
  Firebase.begin(&config, &auth);

  Firebase.setString(fbdo, DEVICE_PATH + "/status", "online");
}

/*************** SETUP ****************/
void setup() {
  Serial.begin(115200);

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass);

  Wire.begin(21, 22);   // SDA, SCL

  Wire.beginTransmission(MPU_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  setupFirebase();

  timer.setInterval(300L, sendIMUToFirebase);

  Serial.println("✅ System Ready");
}

/*************** LOOP + FALL LOGIC ****************/
void loop() {
  Blynk.run();
  timer.run();

  mpu_read();

  float Raw_Amp = sqrt(ax * ax + ay * ay + az * az);
  int Amp = Raw_Amp * 10;

  // ✅ TRIGGER 1 — Free Fall
  if (Amp <= 2 && trigger2 == false) {
    trigger1 = true;
    Serial.println("TRIGGER 1");
  }

  // ✅ TRIGGER 2 — Impact
  if (trigger1 == true) {
    trigger1count++;
    if (Amp >= 12) {
      trigger2 = true;
      trigger1 = false;
      trigger1count = 0;
      Serial.println("TRIGGER 2");
    }
  }

  // ✅ TRIGGER 3 — Orientation Change
  if (trigger2 == true) {
    trigger2count++;
    angleChange = sqrt(gx * gx + gy * gy + gz * gz);

    if (angleChange >= 30 && angleChange <= 400) {
      trigger3 = true;
      trigger2 = false;
      trigger2count = 0;
      Serial.println("TRIGGER 3");
    }
  }

  // ✅ STEP 4 — Confirm Fall
  if (trigger3 == true) {
    trigger3count++;

    if (trigger3count >= 10) {
      angleChange = sqrt(gx * gx + gy * gy + gz * gz);

      if (angleChange >= 0 && angleChange <= 10) {
        fall = true;
        Serial.println("⚠️ FALL DETECTED! ✅");

        Blynk.logEvent("fall_detected", "⚠️ Fall Detected!");
        pushFallEvent();
      }

      trigger3 = false;
      trigger3count = 0;
    }
  }

  // ✅ Timeout resets
  if (trigger2count >= 6) {
    trigger2 = false;
    trigger2count = 0;
  }

  if (trigger1count >= 6) {
    trigger1 = false;
    trigger1count = 0;
  }

  // ✅ Auto-reset fall flag after sending
  if (fall) {
    delay(2000);
    fall = false;
  }

  delay(20);
}
