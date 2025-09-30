from config import USD_TO_RIAL

def format_price(usd_amount: float) -> str:
    """نمایش قیمت دلاری + ریالی"""
    rial_amount = int(usd_amount * USD_TO_RIAL)
    return f"💵 {usd_amount:.2f} USDT\n💰 {rial_amount:,} تومان"
