import os, hmac, hashlib, random, time
from datetime import datetime
import aiohttp
from config import HMAC_SECRET, OTP_TTL_SECONDS, OTP_MAX_ATTEMPTS, OTP_RESEND_COOLDOWN, SMS_PROVIDER, SMS_API_KEY, SMS_TEMPLATE_ID, USD_TO_RIAL, PAY_IR_API_KEY, CALLBACK_HOST
from storage import set_otp, get_otp_record, inc_otp_attempts, clear_otp

# --- OTP helpers ---
def _generate_otp():
    return f"{random.randint(100000, 999999)}"

def _hash_otp(otp: str) -> str:
    return hmac.new(HMAC_SECRET.encode(), otp.encode(), hashlib.sha256).hexdigest()

async def create_and_send_otp(tg_id: int, phone: str):
    rec = get_otp_record(tg_id)
    now_ts = int(time.time())
    if rec and rec.get('last_sent') and now_ts - rec['last_sent'] < OTP_RESEND_COOLDOWN:
        return False, 'cooldown'
    otp = _generate_otp()
    otp_hash = _hash_otp(otp)
    expires = int(time.time()) + OTP_TTL_SECONDS
    set_otp(tg_id, otp_hash, expires, now_ts)
    ok = await _send_sms(phone, otp)
    if not ok:
        return False, 'sms_failed'
    return True, 'sent'

async def verify_otp_code(tg_id: int, code: str):
    rec = get_otp_record(tg_id)
    now_ts = int(time.time())
    if not rec:
        return False, 'no_otp'
    if now_ts > rec['expires_at']:
        clear_otp(tg_id)
        return False, 'expired'
    if rec['attempts'] >= OTP_MAX_ATTEMPTS:
        return False, 'too_many'
    provided_hash = _hash_otp(code)
    if hmac.compare_digest(provided_hash, rec['otp_hash']):
        clear_otp(tg_id)
        return True, 'ok'
    else:
        inc_otp_attempts(tg_id)
        return False, 'wrong'

# --- SMS sending (wrappers) ---
async def _send_sms(phone: str, otp: str) -> bool:
    try:
        if SMS_PROVIDER == 'smsir':
            url = 'https://api.sms.ir/v1/send/verify'
            headers = {'Content-Type':'application/json', 'x-api-key': SMS_API_KEY}
            payload = {
                'mobile': phone,
                'templateId': SMS_TEMPLATE_ID,
                'parameterArray': [{'name':'CODE', 'value': otp}]
            }
            async with aiohttp.ClientSession() as s:
                async with s.post(url, json=payload, headers=headers, timeout=15) as r:
                    return r.status == 200
        elif SMS_PROVIDER == 'kavenegar':
            url = f'https://api.kavenegar.com/v1/{SMS_API_KEY}/sms/send.json'
            data = {'receptor': phone, 'message': f'کد تایید شما: {otp}'}
            async with aiohttp.ClientSession() as s:
                async with s.post(url, data=data, timeout=15) as r:
                    j = await r.json()
                    # kavenegar returns array; success if 'message' present
                    return r.status == 200
        else:
            return False
    except Exception:
        return False

# --- Pay.ir helper ---
async def create_pay_ir_link(amount_rial: float, description: str):
    url = 'https://pay.ir/pg/send'
    payload = {
        'api': PAY_IR_API_KEY or os.getenv('PAY_IR_API_KEY'),
        'amount': int(amount_rial),
        'redirect': CALLBACK_HOST,
        'description': description
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(url, data=payload, timeout=15) as r:
                j = await r.json()
                if j.get('status') == 1:
                    token = j.get('token')
                    return f'https://pay.ir/pg/{token}'
                return None
    except Exception:
        return None

# --- price formatting ---
def format_price(usd_amount: float) -> str:
    rial = int(usd_amount * USD_TO_RIAL)
    return f"💵 {usd_amount:.2f} USD\n💰 {rial:,} تومان"
