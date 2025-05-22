"""
Configuration settings for the OCPP server.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Server settings
HOST = os.getenv('OCPP_HOST', '0.0.0.0')
PORT = int(os.getenv('OCPP_PORT', 9000))

# Logging settings
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Supported OCPP versions
SUPPORTED_PROTOCOLS = ['ocpp1.6']  # We'll add OCPP 2.0.1 later

# Heartbeat settings
DEFAULT_HEARTBEAT_INTERVAL = 300  # 5 minutes in seconds 