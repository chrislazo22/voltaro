
-- Voltaro DB Schema (PostgreSQL, OCPP 1.6 Core Profile)

CREATE TABLE charge_points (
    id SERIAL PRIMARY KEY,
    charge_point_id VARCHAR(64) UNIQUE NOT NULL,
    vendor VARCHAR(128),
    model VARCHAR(128),
    firmware_version VARCHAR(128),
    last_seen TIMESTAMP,
    status VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE connectors (
    id SERIAL PRIMARY KEY,
    charge_point_id INTEGER REFERENCES charge_points(id) ON DELETE CASCADE,
    connector_id INTEGER NOT NULL,
    status VARCHAR(32),
    availability VARCHAR(32),
    last_status_update TIMESTAMP
);

CREATE TABLE id_tags (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(32), -- Accepted, Blocked, etc.
    expiry_date TIMESTAMP,
    parent_tag VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER UNIQUE NOT NULL,
    charge_point_id INTEGER REFERENCES charge_points(id),
    connector_id INTEGER,
    id_tag VARCHAR(64) REFERENCES id_tags(tag),
    meter_start INTEGER,
    meter_stop INTEGER,
    start_timestamp TIMESTAMP,
    stop_timestamp TIMESTAMP,
    status VARCHAR(32)
);

CREATE TABLE meter_values (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    value INTEGER NOT NULL, -- Wh
    measurand VARCHAR(64),
    unit VARCHAR(16)
);

CREATE TABLE configuration (
    id SERIAL PRIMARY KEY,
    key VARCHAR(128) UNIQUE NOT NULL,
    value TEXT
);

CREATE TABLE data_transfers (
    id SERIAL PRIMARY KEY,
    charge_point_id INTEGER REFERENCES charge_points(id),
    vendor_id VARCHAR(128),
    message_id VARCHAR(128),
    data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
