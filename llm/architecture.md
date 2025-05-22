# ⚡ OCPP Backend Architecture (Python)

This document outlines the architecture for a full-stack, scalable EV charging backend system using the Python `ocpp` package.

---

## 🧱 High-Level Architecture

```
             +--------------------+       +------------------+
             |   EV Chargers      | <-->  | OCPP WebSocket    |
             | (OCPP 1.6/2.0.1)   |       | Server (Python)   |
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

---

## ⚙️ Component Breakdown

### 1. OCPP WebSocket Server

- Built with `ocpp` + `websockets`
- Handles OCPP 1.6/2.0.1 messages
- Parses and dispatches message handlers

### 2. Message Handlers

- Python methods decorated with `@on(...)`
- Respond to messages like `BootNotification`, `Authorize`, `StartTransaction`, etc.

### 3. Session Manager

- Tracks transaction state, energy use, session lifecycle

### 4. Database (PostgreSQL)

- Stores charge point data, transactions, meter values, etc.
- Use SQLAlchemy or Tortoise ORM

### 5. Authorization

- Authorizes RFID tags using DB or API
- Responds to `Authorize` requests

### 6. Heartbeat Tracker

- Updates status based on incoming heartbeats

### 7. REST API (FastAPI or Django)

- Exposes data to admin dashboard or external systems

### 8. Admin Dashboard

- View charger status, sessions, history
- Manage users and tags

### 9. Optional: Task Queue (Celery + Redis)

- Background jobs for alerts, invoices, etc.

---

## 🛠 Suggested File Structure

```
voltaro/
├── app/
│   ├── main.py                # Entry point for WebSocket server
│   ├── config.py              # Config management
│   ├── handlers/              # OCPP message handlers
│   │   ├── boot_notification.py
│   │   ├── authorize.py
│   │   └── start_transaction.py
│   ├── services/
│   │   ├── session_manager.py
│   │   ├── heartbeat_tracker.py
│   │   └── authorization.py
│   ├── models/                # ORM models
│   ├── api/                   # REST API endpoints (FastAPI)
│   ├── schemas/               # Pydantic schemas
│   ├── tasks/                 # Optional Celery tasks
│   └── utils/                 # Utilities
├── frontend/                  # React (or other) frontend app
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ✅ MVP Build Order

| Phase | Feature                            |
| ----- | ---------------------------------- |
| 1     | OCPP WebSocket server + handlers   |
| 2     | Session persistence (Postgres)     |
| 3     | Admin UI to view sessions/status   |
| 4     | Authorization + `StartTransaction` |
| 5     | `StopTransaction`, pricing logic   |
| 6     | Webhooks / external APIs           |
| 7     | Billing / Payments                 |

---

## License & Notes

This architecture assumes you're using the [ocpp](https://pypi.org/project/ocpp/) library, which is MIT licensed and commercially usable.
