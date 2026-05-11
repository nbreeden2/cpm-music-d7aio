"""simulate.py SONG.MUS [-o out.wav] [--voices VOICES.MUS]

Faithfully simulate what PLAY.COM would output for SONG.MUS, mixing the
two D+7A DACs into a single mono waveform at the calibrated hardware
sample rate (default 11169 Hz; override via --sample-rate or function arg).

The simulation is sample-accurate:
    phase_n   += step_n              (16-bit add, wraps at 0x10000)
    sample_n   = wavetable[voice_n][phase_n >> 8]
    DAC1       = sample1 + sample2   (signed 8-bit add)
    DAC3       = sample3 + sample4
    speaker    = (DAC1 + DAC3) / 2
"""

import argparse
import struct
import wave


def load_voices(path: str):
    raw = open(path, 'rb').read()
    assert len(raw) == 1536, f'expected 1536 bytes, got {len(raw)}'
    voices = []
    for i in range(6):
        page = raw[i*256:(i+1)*256]
        voices.append(bytes(page))
    return voices


def synth(song_path: str, voices_path: str, out_path: str, sample_rate: int = 11169):
    voices = load_voices(voices_path)

    data = open(song_path, 'rb').read()
    words = list(struct.unpack('<' + 'H' * (len(data)//2), data))

    phase = [0, 0, 0, 0]
    step = [0, 0, 0, 0]
    timbre = [0, 0, 0, 0]
    tempo = 100

    samples = bytearray()  # mono 16-bit signed at sample_rate

    i = 0
    while i < len(words):
        cmd = words[i]; i += 1
        dur = cmd & 0xFF
        bits = (cmd >> 8) & 0xFF
        if dur == 0:
            break
        for b in range(4):
            if bits & (1 << b):
                step[b] = words[i]; i += 1
        if bits & (1 << 4):
            v12 = words[i]; i += 1
            v34 = words[i]; i += 1
            timbre[0] = (v12 & 0xFF) - 0x81
            timbre[1] = (v12 >> 8) - 0x81
            timbre[2] = (v34 & 0xFF) - 0x81
            timbre[3] = (v34 >> 8) - 0x81
            for k in range(4):
                if not 0 <= timbre[k] <= 5:
                    raise ValueError(f'voice {k+1} timbre out of range: {timbre[k]}')
        if bits & (1 << 5):
            tempo = words[i] & 0xFF; i += 1

        # how many samples does this command run for?
        n_samples = dur * tempo
        for _ in range(n_samples):
            s = 0
            for v in range(4):
                phase[v] = (phase[v] + step[v]) & 0xFFFF
                b = voices[timbre[v]][phase[v] >> 8]
                if b >= 128:
                    b -= 256
                s += b
            # s now in roughly +/-240 range (sum of 4 signed 8-bit waves at <=60 each).
            # Scale to 16-bit
            s16 = max(-32768, min(32767, s * 128))
            samples += struct.pack('<h', s16)

    n_frames = len(samples) // 2
    print(f'rendered {n_frames} samples = {n_frames/sample_rate:.2f} sec')
    with wave.open(out_path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(bytes(samples))
    print(f'wrote {out_path}')


def main():
    from _paths import VOICES_MUS
    ap = argparse.ArgumentParser()
    ap.add_argument('song')
    ap.add_argument('--voices', default=str(VOICES_MUS))
    ap.add_argument('-o', '--out', default=None)
    args = ap.parse_args()
    out = args.out or (args.song.rsplit('.', 1)[0] + '_sim.wav')
    synth(args.song, args.voices, out)


if __name__ == '__main__':
    main()
