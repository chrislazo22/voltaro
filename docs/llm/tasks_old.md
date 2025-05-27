# 📋 Voltaro MVP Build Plan

This step-by-step guide outlines the MVP implementation of Voltaro, a full-stack EV charging backend built using the Python `ocpp` package. Each task is designed to be small, testable, and focused on a single concern.

---

## 🚀 Phase 1: WebSocket Server & OCPP Boot Flow

### 1. Create Python project structure

- **Start:** Set up `ocpp_backend/app` directories
- **Middle:** Create `main.py` entry point and add basic logging
- **End:** Confirm directory and file structure matches `architecture.md`

### 2. Install dependencies

- **Start:** Create `requirements.txt` with `ocpp`, `websockets`, `uvicorn`
- **Middle:** Set up virtual environment and install packages
- **End:** Verify with a `pip freeze` and basic `import ocpp`

### 3. Build base WebSocket server

- **Start:** Set up WebSocket server with `websockets.serve`
- **Middle:** Log incoming connections from charge points
- **End:** Test using a mock client that connects

### 4. Implement ChargePoint class

- **Start:** Create `ChargePoint` subclass with `on_boot_notification` handler
- **Middle:** Log incoming `BootNotification` data
- **End:** Respond with `BootNotification.Accepted`

### 5. Run full boot simulation test

- **Start:** Write a test client to send `BootNotification`
- **Middle:** Verify client receives an accepted response
- **End:** Ensure server logs correct request + response

---

## 💾 Phase 2: Persistence Layer

### 6. Add SQLAlchemy and Postgres

- **Start:** Add SQLAlchemy to `requirements.txt`
- **Middle:** Configure DB connection to local Postgres
- **End:** Run a test insert/query with a `charger` model

### 7. Create `ChargePoint` and `Session` models

- **Start:** Define ORM models in `models/`
- **Middle:** Create Alembic migration for tables
- **End:** Verify schema with `psql` or admin tool

### 8. Store BootNotification in DB

- **Start:** Modify handler to insert record into DB
- **Middle:** Add unit test that mocks DB and asserts insert
- **End:** Confirm DB record appears after simulated boot

---

## 📡 Phase 3: Heartbeats and Session State

### 9. Implement Heartbeat handler

- **Start:** Add `on_heartbeat` to ChargePoint
- **Middle:** Update last_seen timestamp in DB
- **End:** Log heartbeat timestamp + return current time

### 10. Track charge point online status

- **Start:** Add status field to ChargePoint model
- **Middle:** Update on connect/heartbeat
- **End:** Query DB to confirm online status changes

---

## 🔐 Phase 4: Authorization + StartTransaction

### 11. Create `id_tag` model/table

- **Start:** Add model with status and expiry fields
- **Middle:** Insert test id_tag records
- **End:** Confirm querying by tag string

### 12. Implement `Authorize` handler

- **Start:** Match incoming tag against DB
- **Middle:** Return accepted or rejected
- **End:** Add unit test for handler logic

### 13. Handle `StartTransaction`

- **Start:** Add handler and validate id_tag
- **Middle:** Store new session in DB with meter_start
- **End:** Return transaction ID and confirm DB insert

---

## 📊 Phase 5: Admin API (FastAPI)

### 14. Set up FastAPI project

- **Start:** Create `api/` folder with `main.py`
- **Middle:** Define GET `/status` and connect to DB
- **End:** Test endpoint returns known charger status

### 15. Add session list endpoint

- **Start:** Create GET `/sessions`
- **Middle:** Return last 10 sessions with duration
- **End:** Test with a real charge point session

---

## ✅ Final Checks

- Write basic integration tests for each message type
- Run docker-compose with Postgres, WebSocket, and FastAPI
- Test full flow: boot → heartbeat → startTransaction → dashboard

---

All tasks are scoped for individual hand-off to an engineering agent or dev.
