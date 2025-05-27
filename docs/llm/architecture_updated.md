
# ⚡ Updated Voltaro Architecture (OCPP 1.6 Core-Compliant)

This architecture aligns with the OCPP 1.6 **Core Profile** and reflects the required operations and data flows necessary for backend compliance. It includes provisions for BootNotification, Authorize, StartTransaction, StopTransaction, MeterValues, and more.

## 🧱 High-Level Architecture

```
             +--------------------+       +------------------+
             |   EV Chargers      | <-->  | OCPP WebSocket    |
             | (OCPP 1.6)         |       | Server (Python)   |
             +--------------------+       +------------------+
                                                    |
                                                    v
                                         +------------------------+
                                         | Message Handlers (OCPP)|
                                         +------------------------+
                                                    |
        +-----------------------------+-------------+----------------------------+
        |                             |                                              |
        v                             v                                              v
+------------------+     +-------------------------+                     +----------------------+
| Session Manager  |     | Authorization & IdTags |                     | Heartbeat Tracker     |
| (Tracks status,  |     | (RFID auth, caching)    |                     | (Online/offline logic)|
| energy, txns)    |     +-------------------------+                     +----------------------+
+--------+---------+
         |
         v
+---------------------+
| Database (Postgres) |
+---------------------+
         |
         v
+-------------------------------+
| REST API / Admin Dashboard   |
| (FastAPI or Django)          |
+-------------------------------+
         |
         v
+--------------------------+
| Frontend (React, etc.)   |
+--------------------------+
```

## ✅ Core Message Coverage

This architecture implements the following Core Profile messages from OCPP 1.6:

- `Authorize`
- `BootNotification`
- `StartTransaction`
- `StopTransaction`
- `Heartbeat`
- `MeterValues`
- `StatusNotification`
- `ChangeAvailability`
- `RemoteStartTransaction`
- `RemoteStopTransaction`
- `Reset`
- `UnlockConnector`
- `ChangeConfiguration`
- `GetConfiguration`
- `ClearCache`
- `DataTransfer`

## 📁 Suggested File Structure

```
voltaro/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── charge_point.py
│   ├── handlers/
│   │   ├── authorize.py
│   │   ├── boot_notification.py
│   │   ├── start_transaction.py
│   │   ├── stop_transaction.py
│   │   ├── heartbeat.py
│   │   ├── metervalues.py
│   │   ├── reset.py
│   │   └── status_notification.py
│   ├── services/
│   │   ├── session_manager.py
│   │   ├── authorization.py
│   │   └── metering.py
│   ├── models/
│   │   └── schema.py
│   ├── api/
│   ├── schemas/
│   ├── utils/
├── tests/
│   └── simulate_client.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```
