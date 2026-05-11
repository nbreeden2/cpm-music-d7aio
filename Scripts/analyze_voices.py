"""
Extract and analyze the wavetable timbres in VOICES.MUS.

The file is concatenated 256-byte single-cycle waveforms, signed 8-bit PCM,
one per timbre. Player references each by its page (high byte of address).
"""

import math
import struct
import wave

from _paths import VOICES_MUS, VOICES_ANALYSIS

SRC = VOICES_MUS
OUT_DIR = VOICES_ANALYSIS
OUT_DIR.mkdir(exist_ok=True)

PAGE = 256
SAMPLE_RATE = 11169  # calibrated against physical D+7A hardware (2026-05-09)


def s8(b: int) -> int:
    """Interpret one byte as signed 8-bit two's complement."""
    return b - 256 if b >= 128 else b


def analyze_table(idx: int, raw: bytes) -> dict:
    samples = [s8(b) for b in raw]

    # amplitude
    pk_pos = max(samples)
    pk_neg = min(samples)
    pk = max(abs(pk_pos), abs(pk_neg))
    rms = math.sqrt(sum(s * s for s in samples) / len(samples))
    dc = sum(samples) / len(samples)

    # zero crossings (in one cycle = number of half-periods seen at top harmonic)
    zc = 0
    for i in range(len(samples)):
        a, b = samples[i - 1], samples[i]
        if (a < 0 and b >= 0) or (a >= 0 and b < 0):
            zc += 1

    # naive harmonic content via DFT magnitudes (single cycle = bin k is the kth harmonic)
    N = len(samples)
    mags = []
    for k in range(1, 17):  # first 16 harmonics is plenty
        re = sum(samples[n] * math.cos(-2 * math.pi * k * n / N) for n in range(N))
        im = sum(samples[n] * math.sin(-2 * math.pi * k * n / N) for n in range(N))
        mags.append(math.sqrt(re * re + im * im) / (N / 2))

    return {
        "idx": idx,
        "pk_pos": pk_pos,
        "pk_neg": pk_neg,
        "pk": pk,
        "rms": rms,
        "dc": dc,
        "zero_crossings": zc,
        "harmonics": mags,
    }


def write_wav(idx: int, raw: bytes):
    """Render this single-cycle table as a 1-second WAV at 220 Hz so the ear
    can hear it. Plays back at SAMPLE_RATE Hz with phase-accumulator playback
    identical to PLAY.COM."""
    freq = 220.0
    step = round(freq * 65536 / SAMPLE_RATE)
    nsamples = SAMPLE_RATE  # 1 second
    phase = 0
    out = bytearray()
    samples = [s8(b) for b in raw]
    for _ in range(nsamples):
        phase = (phase + step) & 0xFFFF
        # PLAY.COM does ADD A,(HL) on signed 8-bit; we scale ×512 to s16 here
        out += struct.pack("<h", samples[phase >> 8] * 256)
    wav_path = OUT_DIR / f"voice{idx}_220Hz.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(out))
    return wav_path


def write_table_dump(idx: int, raw: bytes):
    """ASCII waveform table dump."""
    samples = [s8(b) for b in raw]
    path = OUT_DIR / f"voice{idx}.txt"
    with open(path, "w") as f:
        f.write(f"# VOICES.MUS — voice {idx} (page {0x07 + idx:02X}h in PLAY.COM)\n")
        f.write("# offset  sgn  scaled position\n")
        for i, s in enumerate(samples):
            bar_pos = "." * (s + 64) if s >= -64 else ""
            bar = bar_pos.ljust(128)
            f.write(f"  {i:3d}  {s:+4d}  {bar}\n")
    return path


def write_csv(tables_data):
    """Spreadsheet-friendly dump: one column per voice, 256 rows."""
    csv_path = OUT_DIR / "all_voices.csv"
    with open(csv_path, "w") as f:
        f.write("phase," + ",".join(f"voice{i}" for i in range(len(tables_data))) + "\n")
        for ph in range(PAGE):
            row = [str(ph)]
            for raw in tables_data:
                row.append(str(s8(raw[ph])))
            f.write(",".join(row) + "\n")
    return csv_path


def main():
    data = SRC.read_bytes()
    n_tables = len(data) // PAGE
    print(f"VOICES.MUS = {len(data)} bytes = {n_tables} × {PAGE}-byte tables\n")

    tables = [data[i * PAGE : (i + 1) * PAGE] for i in range(n_tables)]
    analyses = [analyze_table(i, t) for i, t in enumerate(tables)]

    # textual summary — absolute harmonic magnitudes (not normalized)
    print(
        f"{'V':<2} {'Page':<5} {'pk+':<4} {'pk-':<4} {'pk':<3} {'RMS':<5} "
        f"{'DC':<5} {'ZC':<3}  H1   H2   H3   H4   H5   H6   H7   H8"
    )
    print("-" * 100)
    for a in analyses:
        h = a["harmonics"]
        h_str = " ".join(f"{v:4.1f}" for v in h[:8])
        print(
            f"{a['idx']:<2} 0x{0x07 + a['idx']:02X}  "
            f"{a['pk_pos']:+4d} {a['pk_neg']:+4d} {a['pk']:3d} "
            f"{a['rms']:5.1f} {a['dc']:+5.2f} {a['zero_crossings']:3d}  {h_str}"
        )

    # dump everything
    print(f"\nWriting per-voice ASCII tables, WAVs, and combined CSV to {OUT_DIR}/")
    for i, t in enumerate(tables):
        write_table_dump(i, t)
        write_wav(i, t)
    write_csv(tables)
    print("Done.")


if __name__ == "__main__":
    main()
