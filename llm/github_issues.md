# ✅ Voltaro MVP GitHub Issue Templates

## 🚀 `Create Python project structure`

### Goal

Set up `voltaro/app` directory structure with base files.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Install dependencies`

### Goal

Add `ocpp`, `websockets`, and `uvicorn` to requirements and verify installation.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Build base WebSocket server`

### Goal

Create a minimal async server that accepts connections.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Implement ChargePoint class`

### Goal

Create subclass with `on_boot_notification` handler.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Run full boot simulation test`

### Goal

Send BootNotification using a simulated client and assert correct response.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Add SQLAlchemy and Postgres`

### Goal

Set up database connection and run a test query.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Create ChargePoint and Session models`

### Goal

Define ORM models and apply migrations.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Store BootNotification in DB`

### Goal

Persist boot info on reception and confirm via query.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Implement Heartbeat handler`

### Goal

Log heartbeat and update `last_seen` timestamp.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Track charge point online status`

### Goal

Update DB field for status based on heartbeat.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Create id_tag model/table`

### Goal

Add support for authorization via RFID tags.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Implement Authorize handler`

### Goal

Lookup id_tag and return accepted/rejected.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Handle StartTransaction`

### Goal

Store session with `transaction_id` and meter data.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Set up FastAPI project`

### Goal

Expose status endpoint from Postgres.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---

## 🚀 `Add session list endpoint`

### Goal

Return sessions via REST API.

### Checklist

- [ ] Break the task into implementation steps
- [ ] Write unit or integration tests
- [ ] Confirm functionality manually or via test script

### Definition of Done

- All checklist items complete and passing

---
