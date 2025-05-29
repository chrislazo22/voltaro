# Voltaro OCPP Backend

A Python-based OCPP (Open Charge Point Protocol) backend server for EV charging stations.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- PostgreSQL (for database)

### Installation

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp env.example .env
# Edit .env with your database credentials
```

### Running the Server

1. Start the OCPP WebSocket server:

```bash
python app/main.py
```

The server will start on `ws://0.0.0.0:9000` by default.

## 🧪 Testing

### End-to-End Testing

1. Start the server:
```bash
python app/main.py
```

2. In another terminal, run the mock client:
```bash
python tests/mock_client.py
```

### Database Testing

Set up test data:
```bash
python tests/setup_test_tags.py
```

Verify specific functionality:
```bash
python tests/test_boot_notification_db.py
python tests/test_start_transaction_db.py
python tests/test_stop_transaction_db.py
```

See `tests/README.md` for detailed testing documentation.

## 📝 Project Structure

```
voltaro/
├── app/
│   ├── main.py                # Entry point for WebSocket server
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database connection and session management
│   ├── handlers/
│   │   └── charge_point.py    # OCPP message handlers
│   └── models/
│       └── schema.py          # SQLAlchemy database models
├── tests/                     # Test files and mock clients
│   ├── README.md              # Testing documentation
│   ├── mock_client.py         # OCPP mock charge point client
│   ├── setup_test_tags.py     # Test data setup
│   └── test_*.py              # Database verification scripts
├── scripts/                   # Utility scripts
│   └── recreate_tables.py     # Database schema management
├── docs/                      # Documentation and OCPP specs
├── logs/                      # Log files
└── README.md
```

## 🔌 OCPP 1.6 Support

Currently implemented OCPP 1.6 Core Profile messages:
- ✅ BootNotification
- ✅ Heartbeat
- ✅ Authorize
- ✅ StartTransaction
- ✅ MeterValues
- ✅ StopTransaction

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

