"""decode_mus.py FILE [--limit N]

Pretty-print a .MUS song as the sequence of commands the player would see.

The file is a stream of little-endian 16-bit words pushed onto the song
stack.  Each command is one word ('cmd') whose low byte is the duration
(0 = end-of-song) and whose high byte is a bitmap selecting which of the
following 0..7 words are payload:

    bit 0 -> v1 phase increment      bit 1 -> v2 phase increment
    bit 2 -> v3 phase increment      bit 3 -> v4 phase increment
    bit 4 -> two voice-byte words    bit 5 -> tempo word (low byte used)

Voice-byte word packs two timbre selectors: lo = first voice, hi = next.
Voice-byte encoding = 0x81 + table_index (0..5).
"""

import argparse
import struct
import sys


def step_to_note(s: int, sample_rate: int = 11169) -> str:
    if s == 0:
        return '   -   '
    freq = s * sample_rate / 65536.0
    import math
    semis = round(math.log2(freq / 440.0) * 12)
    octv = 4 + (semis + 9) // 12
    name = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][(semis + 9) % 12]
    err_cents = round((math.log2(freq / 440.0) * 12 - semis) * 100)
    if err_cents == 0:
        return f'{name}{octv}'.ljust(7)
    return f'{name}{octv}{err_cents:+d}c'.ljust(7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--limit', type=int, default=None)
    args = ap.parse_args()

    data = open(args.file, 'rb').read()
    words = list(struct.unpack('<' + 'H' * (len(data)//2), data))

    print(f'{args.file}: {len(data)} bytes, {len(words)} words\n')
    print(f'{"#":>4} {"cmd":>5} {"bits":>8} {"dur":>4}  '
          f'{"v1_pitch":>10} {"v2_pitch":>10} '
          f'{"v3_pitch":>10} {"v4_pitch":>10}  '
          f'{"v1_v2":>10} {"v3_v4":>10} {"tempo":>5}')
    print('-' * 130)

    n = 0
    state = ['-'] * 4   # last seen pitch per voice (display only)
    timbres = ['-', '-', '-', '-']
    tempo = '-'
    i = 0
    total_samples = 0
    while i < len(words):
        cmd = words[i]; i += 1
        dur = cmd & 0xFF
        bits = (cmd >> 8) & 0xFF
        if dur == 0:
            print(f'{n:>4} {cmd:>05X}  END (dur=0)')
            break

        cells = ['', '', '', '', '', '', '']
        for b in range(4):
            if bits & (1 << b):
                p = words[i]; i += 1
                state[b] = step_to_note(p)
                cells[b] = f'{p:04X}={state[b]}'
            else:
                cells[b] = state[b].rjust(10)
        if bits & (1 << 4):
            v12 = words[i]; i += 1
            v34 = words[i]; i += 1
            timbres[0] = (v12 & 0xFF) - 0x81
            timbres[1] = (v12 >> 8) - 0x81
            timbres[2] = (v34 & 0xFF) - 0x81
            timbres[3] = (v34 >> 8) - 0x81
            cells[4] = f'{timbres[0]},{timbres[1]}'.rjust(10)
            cells[5] = f'{timbres[2]},{timbres[3]}'.rjust(10)
        else:
            cells[4] = '-'.rjust(10)
            cells[5] = '-'.rjust(10)
        if bits & (1 << 5):
            tempo_w = words[i]; i += 1
            tempo = tempo_w & 0xFF
            cells[6] = f'{tempo}'.rjust(5)
        else:
            cells[6] = '-'.rjust(5)

        ms = dur * (tempo if isinstance(tempo, int) else 100) / 11169 * 1000
        total_samples += dur * (tempo if isinstance(tempo, int) else 100)

        print(f'{n:>4} {cmd:>05X} {bits:>08b} {dur:>4}  '
              f'{cells[0]} {cells[1]} {cells[2]} {cells[3]}  '
              f'{cells[4]} {cells[5]} {cells[6]}'
              f'   ({ms:.0f}ms)')
        n += 1
        if args.limit is not None and n >= args.limit:
            print(f'... (stopped at --limit {args.limit})')
            return

    print()
    print(f'total commands: {n}')
    print(f'total samples:  {total_samples}  ({total_samples/11169:.2f} sec at 11169 Hz)')


if __name__ == '__main__':
    main()
