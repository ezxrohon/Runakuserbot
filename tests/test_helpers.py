import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from runak.helpers import calculate, small_caps, fmt_duration, _SMALL

assert calculate("12 * (3 + 2)") == 60
assert calculate("-4 + 10 / 4") == -1.5
for bad in ["__import__('os')", "2 ** 999", "(1).__class__", "True + 1", "a + 1", "1" * 200]:
    try:
        calculate(bad)
    except Exception:
        pass
    else:
        raise AssertionError(f"should have rejected: {bad!r}")
assert len(_SMALL) == 26
assert small_caps("Runak") == "ʀᴜɴᴀᴋ"
assert fmt_duration(3725) == "1h 2m 5s"
print("helpers OK")

from runak.helpers import FONTS, parse_duration
assert parse_duration("1h30m") == 5400 and parse_duration("45s") == 45 and parse_duration("2d") == 172800
for bad in ["", "soon", "10", "5x", "1h 30m", "m5"]:
    assert parse_duration(bad) is None, bad
assert FONTS["bold"]("Hi 1") == "𝐇𝐢 1"
assert FONTS["circle"]("a") == "ⓐ" and FONTS["mono"]("a") == "𝚊"
print("helpers+ OK")
