import os
from pathlib import Path

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')  # required
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
LOG_CHANNEL = os.getenv('LOG_CHANNEL')  # optional (channel id as string)

# Pay.ir
PAY_IR_API_KEY = os.getenv('PAY_IR_API_KEY')
CALLBACK_HOST = os.getenv('CALLBACK_HOST', 'https://example.com')  # used as redirect in pay.ir

# SMS provider: 'smsir' or 'kavenegar'
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'smsir')
SMS_API_KEY = os.getenv('SMS_API_KEY')
SMS_TEMPLATE_ID = int(os.getenv('SMS_TEMPLATE_ID', '0'))  # for sms.ir template id

# OTP / security
HMAC_SECRET = os.getenv('HMAC_SECRET', 'replace-this-with-a-random-string')
OTP_TTL_SECONDS = int(os.getenv('OTP_TTL_SECONDS', '180'))  # 3 minutes default
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', '5'))
OTP_RESEND_COOLDOWN = int(os.getenv('OTP_RESEND_COOLDOWN', '60'))  # seconds

# FX
USD_TO_RIAL = float(os.getenv('USD_TO_RIAL', '126000'))

# Storage
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'vouchi.sqlite'

# Debug
DEBUG = os.getenv('DEBUG', '0') == '1'
