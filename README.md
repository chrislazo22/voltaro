# Voltaro OCPP Backend

A Python-based OCPP (Open Charge Point Protocol) backend server for EV charging stations.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)

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

### Running the Server

1. Start the OCPP WebSocket server:

```bash
python -m app.main
```

The server will start on `ws://0.0.0.0:9000` by default.

### Configuration

Create a `.env` file in the project root to override default settings:

```env
OCPP_HOST=0.0.0.0
OCPP_PORT=9000
LOG_LEVEL=INFO
```

## 🧪 Testing

Run the test suite:

```bash
pytest
```

## 📝 Project Structure

```
voltaro/
├── app/
│   ├── main.py                # Entry point for WebSocket server
│   ├── config.py              # Configuration settings
│   ├── handlers/              # OCPP message handlers (coming soon)
│   ├── services/              # Business logic services (coming soon)
│   ├── models/                # Database models (coming soon)
│   └── utils/                 # Utility functions (coming soon)
├── tests/                     # Test directory (coming soon)
├── logs/                      # Log files
└── README.md
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

