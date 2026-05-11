"""Check whether voice 3 (or any other voice) has internal symmetries
that would explain the 'going backwards' visual impression."""
from _paths import VOICES_MUS

PAGE = 256
SRC = VOICES_MUS


def s8(b): return b - 256 if b >= 128 else b


data = SRC.read_bytes()

for idx in range(6):
    samples = [s8(b) for b in data[idx * PAGE : (idx + 1) * PAGE]]

    # Test 1: even symmetry around middle?     samples[i] == samples[256-i]
    # Test 2: odd symmetry around middle?      samples[i] == -samples[256-i]
    # Test 3: half-period sign-flip?           samples[i+128] == -samples[i]
    # Test 4: half-period time-reverse + flip? samples[i+128] == -samples[127-i]
    # Test 5: half-period time-reverse?        samples[i+128] == samples[127-i]
    tests = {
        "even   sym (s[i] == s[256-i])"      : lambda i: samples[i] == samples[(PAGE - i) % PAGE],
        "odd    sym (s[i] == -s[256-i])"     : lambda i: samples[i] == -samples[(PAGE - i) % PAGE],
        "halfA  s[i+128] == -s[i]"            : lambda i: samples[i + 128] == -samples[i] if i < 128 else True,
        "halfB  s[i+128] == -s[127-i]"        : lambda i: samples[i + 128] == -samples[127 - i] if i < 128 else True,
        "halfC  s[i+128] == s[127-i]"         : lambda i: samples[i + 128] == samples[127 - i] if i < 128 else True,
    }

    print(f"\nVoice {idx} (page 0x{0x07+idx:02X}):")
    for name, fn in tests.items():
        matches = sum(1 for i in range(PAGE) if fn(i))
        total = PAGE if "halfA" not in name and "halfB" not in name and "halfC" not in name else 128
        print(f"  {name:38s}  {matches:3d}/{total:3d}  {'YES' if matches == total else ''}")
