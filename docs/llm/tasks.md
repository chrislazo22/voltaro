# 📋 Voltaro MVP Build Plan (Updated for OCPP 1.6 Core Compliance)

Each task is small, testable, and focused on a single feature or message defined in the OCPP 1.6 Core Profile.

---

## 🚀 Phase 1: Setup & Boot Flow

### 1. Create Python project structure

- Create `voltaro/app` folder with `main.py` and `__init__.py`
- Add README and empty `requirements.txt`

### 2. Install dependencies

- Install `ocpp==2.0.0`, `websockets==10.4`
- Verify imports work in `main.py`

### 3. Build base WebSocket server

- Accept incoming WebSocket connections
- Log new charge point connections

### 4. Implement ChargePoint class

- Add `on_boot_notification()` with logging
- Return valid `BootNotification` response

### 5. Run full boot simulation test

- Use a Python client to send a `BootNotification`
- Confirm response and logs

---

## 💾 Phase 2: Database Integration

### 6. Add SQLAlchemy and Postgres config

- Configure DB connection and create engine

### 7. Create models for charge points and sessions

- Define tables for ChargePoint, Session, IdTag, MeterValue

### 8. Store BootNotification in DB

- Persist charge point metadata (vendor/model, status)

---

## 🔄 Phase 3: Core Message Support

### 9. Handle Heartbeat

- Update `last_seen` timestamp in DB
- Return current time

### 10. Handle Authorize

- Lookup `id_tag` in DB
- Accept or reject based on tag status

### 11. Handle StartTransaction

- Record session start time, connector, meter_start
- Link to authorized `id_tag`

### 12. Handle MeterValues

- Store energy usage and timestamps per connector

### 13. Handle StopTransaction

- Update session with `meter_stop`, end time
- Mark session as complete

### 14. Handle StatusNotification

- Track charge point and connector status

---

## ⚙️ Phase 4: Operational Commands

### 15. Handle RemoteStartTransaction

- Accept `id_tag`, trigger StartTransaction logic

### 16. Handle RemoteStopTransaction

- Lookup active session by transaction_id
- Trigger StopTransaction

### 17. Handle ChangeAvailability

- Update connector availability state

### 18. Handle Reset

- Mark charger as rebooting
- Respond accordingly

### 19. Handle UnlockConnector

- Log unlock attempt and result

---

## 🔧 Phase 5: Configuration Commands

### 20. Handle ChangeConfiguration

- Update config key-value in DB

### 21. Handle GetConfiguration

- Return stored config values

### 22. Handle ClearCache

- Clear authorization cache

### 23. Handle DataTransfer

- Accept custom vendor messages, log for debugging

---

## 🌐 Phase 6: REST API & Dashboard

### 24. Set up FastAPI project

- Add `/status`, `/sessions`, `/charge_points` endpoints

### 25. Expose session logs

- Return latest sessions with energy and status

---

## ✅ Finalization

- Add integration tests for each message
- Dockerize services: API, WebSocket, Postgres
- Simulate charger sessions from boot → stop

---

This updated plan ensures Voltaro aligns with the full OCPP 1.6 Core Profile.
