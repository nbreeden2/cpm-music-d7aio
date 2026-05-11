#!/usr/bin/env python3
"""
Disassemble PLAY.COM (Z80, CP/M COM file at 0x100).

Produces an annotated listing with:
  - hand-curated data ranges (FCB, strings, variable area)
  - labels at known entry points and BDOS calls
  - inline comments for self-modifying-code targets
"""

from z80dis import z80

from _paths import PLAY_COM

PATH = str(PLAY_COM)
LOAD = 0x100

with open(PATH, "rb") as f:
    data = f.read()

# Hand-curated data ranges (FILE OFFSETS).
# Everything else is treated as code.
DATA_RANGES = [
    (0x01CD, 0x01D0, "init data: tempo defaults / counters"),
    (0x01D1, 0x01EE, "FCB for VOICES.MUS (drive=0, name='VOICES  ', ext='MUS', + open scratch area)"),
    (0x01EF, 0x045A, "$-terminated message strings"),
    (0x045B, 0x0461, "static variables area (0x055B..0x0561)"),
]

# Labels. Maps memory address -> label name (for cross-references).
LABELS = {
    0x0005: "BDOS",
    0x005C: "FCB",
    0x005D: "FCB+1 (filename byte 0)",
    0x0080: "DMA",
    0x0000: "WBOOT",
    0x0006: "BDOS_VEC",

    # Routines (memory addresses)
    0x0103: "main",
    0x0135: "ask_song",
    0x013E: "open_song",
    0x015B: "ask_params_loop",
    0x0185: "exit_with_msg",
    0x018B: "err_voices",
    0x0190: "err_notfound",
    0x0198: "param_change",
    0x022E: "print_de_then_byte",   # prints msg then 2-digit decimal in A
    0x0264: "print_DE_msg",         # prefixed by setting C=9
    0x0267: "print_msg",            # entry: DE = $-terminated string
    0x026C: "read_console_buf",
    0x0279: "parse_console_to_FCB",
    0x0286: "load_file_loop",       # reads file 128 bytes/record into HL+
    0x029B: "ask_yes_no",           # prints DE prompt, returns Z if Y
    0x02AB: "prompt_decimal",       # prompts and parses decimal → A
    0x02CD: "tmp_digit",            # 1-byte scratch in number printer
    0x02CE: "div10_table",          # 2 bytes: divisor for 2-digit print
    0x02D1: "FCB_VOICES",
    0x02F0: "msg_banner",
    0x0342: "msg_song_file_q",
    0x034E: "msg_play_again",
    0x0363: "msg_new_song",
    0x036E: "msg_change_params",
    0x039E: "msg_repetitions_q",
    0x03B6: "msg_change_part1",
    0x03C6: "msg_change_part2",
    0x03D6: "msg_change_part3",
    0x03E6: "msg_change_part4",
    0x03F6: "msg_change_tempo",
    0x0406: "msg_present_voice1",
    0x0421: "msg_present_voice2",
    0x043D: "msg_present_voice3",
    0x0459: "msg_present_voice4",
    0x0475: "msg_new_voice1",
    0x048D: "msg_new_voice2",
    0x04A5: "msg_new_voice3",
    0x04BD: "msg_new_voice4",
    0x04D5: "msg_present_tempo",
    0x04F0: "msg_new_tempo",
    0x0506: "msg_file_not_found",
    0x0517: "msg_song_too_long",
    0x0537: "msg_cant_load_voices",
    0x054B: "msg_bye",

    # variable area
    0x055B: "voice_offset",         # 1 byte: 0x81 - load_page (subtracted from voice byte to get page)
    0x055C: "song_addr",            # 2 bytes: start of song buffer (= end of VOICES area)
    0x055E: "buf_base",             # 2 bytes: load address basis for VOICES.MUS (rounded up by INC H, LD L,0)
    0x0560: "saved_sp",             # 2 bytes: caller's SP (saved at PLAY entry)

    # PLAY routine
    0x0562: "play_song",            # entry to playback
    0x0579: "next_command",         # POP BC; if C==0 song ends
    0x0584: "dispatch_command",     # B's bits select what to update
    0x05DA: "outer_iter",           # entry: LD B, n (tempo immediate)
    0x05DC: "inner_loop",           # 4-voice phase-accumulator + DAC writes
    0x05E0: "v1_step_imm",          # patched: voice 1 step (LD DE,nn immediate)
    0x05E8: "v1_page_imm",          # patched: voice 1 page (LD H,n immediate)
    0x05EE: "v2_step_imm",
    0x05F6: "v2_page_imm",
    0x05FE: "v3_step_imm",
    0x0606: "v3_page_imm",
    0x060C: "v4_step_imm",
    0x0614: "v4_page_imm",
    0x05DB: "tempo_imm",            # patched: B initial value (LD B,n immediate)

    # the big duplicate block — appears unused at runtime
    0x0623: "dead_code_or_alt_dispatch",
}

def in_data(off):
    for s, e, descr in DATA_RANGES:
        if s <= off <= e:
            return s, e, descr
    return None

def label_for(addr):
    return LABELS.get(addr, "")

def fmt_operand(s):
    """Replace numeric addresses in operand strings with labels where helpful."""
    import re
    def sub(m):
        a = int(m.group(0), 16)
        if a in LABELS:
            return f"{m.group(0)}<{LABELS[a]}>"
        return m.group(0)
    return re.sub(r"0x[0-9a-fA-F]{2,4}", sub, s)

print(f"; PLAY.COM disassembly")
print(f"; File: {PATH}")
print(f"; Size: {len(data)} bytes (0x{len(data):X}), load address: 0x{LOAD:04X}")
print(f"; Disassembled with z80dis; data ranges hand-marked.")
print(f";")
print(f"; Memory layout summary:")
print(f";   0x0100..0x01CC  initial code section (entry, main UI loop)")
print(f";   0x01CD..0x01D0  init values for number-print routine")
print(f";   0x01D1..0x01EE  FCB for VOICES.MUS (used at startup)")
print(f";   0x01EF..0x045A  message strings ($-terminated for BDOS fn 9)")
print(f";   0x045B..0x0461  static variables (voice_offset, song_addr, buf_base, saved_sp)")
print(f";   0x0462..0x0622  play routine and synthesis loop")
print(f";   0x0623..0x067F  appears to be a duplicate of part of 0x05A1..0x05FF (dead/unused)")
print(f";")
print(f"; I/O ports used:")
print(f";   OUT (0x19), A   — Cromemco D+7A I/O analog channel 1 (voices 1+2 mixed)")
print(f";   OUT (0x1B), A   — Cromemco D+7A I/O analog channel 3 (voices 3+4 mixed)")
print(f";")
print(f"; BDOS calls used (function in C, parameters in DE):")
print(f";   09  print $-terminated string at DE")
print(f";   0A  read console buffer at DE (DE+0=max, DE+1=actual, DE+2..=text)")
print(f";   0F  open file (FCB at DE)")
print(f";   14  read sequential record (FCB at DE)")
print(f";   1A  set DMA address to DE")
print(f";   86  (custom?) - unusual; called once at 0x0281 with DE=FCB")
print(f";")
print()

i = 0
while i < len(data):
    addr = LOAD + i
    rng = in_data(i)
    if rng:
        s, e, descr = rng
        # Print one header per data range when entering it.
        if i == s:
            print(f"; --- DATA: {descr} ---")
        # emit a DB line for this data range, 16 bytes per row.
        chunk_end = min(i + 16, e + 1)
        chunk = data[i:chunk_end]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        # Show printable ASCII
        txt = "".join(chr(b) if 0x20 <= b <= 0x7e else "." for b in chunk)
        lbl = label_for(addr)
        prefix = f"{lbl}: " if lbl else ""
        print(f"{addr:04X}: {hex_part:<48s}  ; {prefix}{txt}")
        i = chunk_end
        if i > e:
            print()
        continue
    # Code disassembly
    try:
        d = z80.decode(data[i:i+4], addr)
        ln = d.len
        if ln == 0 or ln > 4:
            ln = 1
        ins = z80.disasm(data[i:i+ln], addr)
        bytes_str = " ".join(f"{b:02X}" for b in data[i:i+ln])
        lbl = label_for(addr)
        if lbl:
            print(f"\n{lbl}:")
        print(f"{addr:04X}: {bytes_str:<14s}  {fmt_operand(ins)}")
        i += ln
    except Exception as ex:
        print(f"{addr:04X}: {data[i]:02X}              ; ?? ({ex})")
        i += 1
