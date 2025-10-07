from utils import _hash_otp
def test_hash_consistency():
    otp = '123456'
    h1 = _hash_otp(otp)
    h2 = _hash_otp(otp)
    assert h1 == h2
    assert isinstance(h1, str)
