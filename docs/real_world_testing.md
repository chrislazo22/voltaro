# Real-World Testing Guide

## Option 1: SteVe OCPP Simulator (Recommended for Development)

### Setup SteVe
```bash
# 1. Install Java 11+
brew install openjdk@11  # macOS
# sudo apt install openjdk-11-jdk  # Ubuntu

# 2. Clone and build SteVe
git clone https://github.com/steve-community/steve.git
cd steve
./mvnw clean package -DskipTests

# 3. Run SteVe
java -jar target/steve-*.jar
```

### Configure SteVe to Connect to Your Backend
1. Open SteVe web interface: http://localhost:8080/steve
2. Go to "Charge Points" → "Add Charge Point"
3. Set:
   - Charge Point ID: `STEVE-CP-001`
   - OCPP Version: `1.6`
   - Central System URL: `ws://localhost:9000/STEVE-CP-001`

### Test Remote Start
1. In SteVe: Go to "Operations" → "Remote Start Transaction"
2. Select charge point: `STEVE-CP-001`
3. ID Tag: `VALID001`
4. Connector ID: `1`
5. Click "Send"

Your Voltaro frontend will show the charge point and you can control it!

## Option 2: Physical Charge Points

### Popular OCPP 1.6 Compatible Hardware
- **Wallbox Pulsar Plus** (~$600) - WiFi enabled, OCPP 1.6
- **KEBA KeContact P30** (~$800) - Industrial grade
- **ABB Terra AC** (~$1200) - Commercial grade
- **Schneider EVlink** (~$900) - Reliable brand

### Configuration Example (Wallbox Pulsar Plus)
```json
{
  "ocpp": {
    "enabled": true,
    "version": "1.6",
    "url": "ws://yourdomain.com:9000/",
    "charge_point_id": "WALLBOX-001",
    "heartbeat_interval": 300
  }
}
```

## Option 3: DIY Charge Point (Advanced)

### ESP32 OCPP Charge Point
```cpp
// Arduino/ESP32 code example
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>

const char* ssid = "your-wifi";
const char* password = "your-password";
const char* ocpp_server = "yourdomain.com";
const int ocpp_port = 9000;
const char* charge_point_id = "ESP32-CP-001";

WebSocketsClient webSocket;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  webSocket.begin(ocpp_server, ocpp_port, "/ESP32-CP-001");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_CONNECTED:
      Serial.println("WebSocket Connected");
      sendBootNotification();
      break;
    case WStype_TEXT:
      handleOCPPMessage((char*)payload);
      break;
  }
}

void sendBootNotification() {
  DynamicJsonDocument doc(1024);
  doc[0] = 2; // CALL
  doc[1] = "boot-001"; // Message ID
  doc[2] = "BootNotification";
  doc[3]["chargePointVendor"] = "DIY";
  doc[3]["chargePointModel"] = "ESP32-CP";
  
  String message;
  serializeJson(doc, message);
  webSocket.sendTXT(message);
}
```

## Option 4: Cloud Testing Services

### OCPP Testing Platforms
- **EV Charging Solutions Testing** - ocpp-test.com
- **ChargePoint API Testing** - chargepoint.com/developers
- **Gridwiz OCPP Cloud** - Professional testing suite

## Making Your Backend Public

### Quick Testing with ngrok
```bash
# Install ngrok
brew install ngrok  # macOS
# snap install ngrok  # Linux

# Expose your backend
ngrok tcp 9000

# Use the URL: tcp://0.tcp.ngrok.io:12345
# Configure charge point to connect to this URL
```

### Production Deployment
```bash
# Deploy to cloud with Docker
docker build -t voltaro-api .
docker run -p 9000:9000 voltaro-api

# Or use cloud services:
# - AWS ECS/Fargate
# - DigitalOcean App Platform  
# - Google Cloud Run
# - Railway.app
```

## Testing Checklist

### ✅ Basic OCPP Compliance
- [ ] BootNotification accepted
- [ ] Heartbeat working (every 300s)
- [ ] StatusNotification handling
- [ ] RemoteStartTransaction → StartTransaction flow
- [ ] RemoteStopTransaction → StopTransaction flow

### ✅ Advanced Features  
- [ ] Authorize requests
- [ ] MeterValues during charging
- [ ] ChangeAvailability
- [ ] Reset commands
- [ ] FirmwareUpdate (if supported)

### ✅ Error Handling
- [ ] Network disconnection recovery
- [ ] Invalid ID tag handling
- [ ] Connector faults
- [ ] Transaction timeouts

## Real Charge Point Behavior vs Mock

| Feature | Mock Client | Real Charge Point |
|---------|-------------|-------------------|
| **Connection** | Instant | May take 30-60s to boot |
| **Authorization** | Simulated | Real RFID/App validation |
| **Charging** | Fake meter values | Real energy measurement |
| **Status Updates** | Immediate | Based on physical state |
| **Error Handling** | Programmed responses | Real fault conditions |
| **Firmware** | N/A | Actual firmware updates | 