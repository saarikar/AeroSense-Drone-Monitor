#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

const char* ssid     = "ESP32_Drone";
const char* password = "12345678";

WiFiServer server(80);
Adafruit_BME680 bme;
const int gasPin = 34;

// ── Cached sensor values (updated in background) ──
float cached_temp = 0, cached_hum = 0, cached_pres = 0, cached_gas1 = 0;
int   cached_gas2 = 0;
unsigned long lastReading = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  bme.begin();
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setGasHeater(320, 150);

  WiFi.softAP(ssid, password);
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());   // usually 192.168.4.1
  server.begin();

  // Prime the first reading before any client arrives
  bme.performReading();
  cached_temp = bme.temperature;
  cached_hum  = bme.humidity;
  cached_pres = bme.pressure / 100.0;
  cached_gas1 = bme.gas_resistance / 1000.0;
  cached_gas2 = analogRead(gasPin);
  lastReading = millis();
}

void loop() {
  // ── 1. Refresh sensor every 2 s (non-blocking check) ──
  if (millis() - lastReading > 2000) {
    if (bme.performReading()) {
      cached_temp = bme.temperature;
      cached_hum  = bme.humidity;
      cached_pres = bme.pressure / 100.0;
      cached_gas1 = bme.gas_resistance / 1000.0;
      cached_gas2 = analogRead(gasPin);
    }
    lastReading = millis();
  }

  // ── 2. Serve any waiting client immediately ──
  WiFiClient client = server.available();
  if (!client) return;

  // Drain the incoming HTTP request (don't block on it)
  unsigned long t0 = millis();
  while (client.connected() && millis() - t0 < 200) {
    if (client.available()) client.read();
    else break;
  }

  // Build JSON from cached values
  String json = "{";
  json += "\"temp\":"  + String(cached_temp, 2) + ",";
  json += "\"hum\":"   + String(cached_hum,  2) + ",";
  json += "\"pres\":"  + String(cached_pres, 2) + ",";
  json += "\"gas1\":"  + String(cached_gas1, 2) + ",";
  json += "\"gas2\":"  + String(cached_gas2);
  json += "}";

  // Send with Connection: close so the client knows the response is complete
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: application/json");
  client.println("Connection: close");
  client.print("Content-Length: ");
  client.println(json.length());
  client.println();
  client.print(json);
  client.flush();
  delay(10);
  client.stop();
}