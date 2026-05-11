#!/usr/bin/env python3
"""
disasm_m80.py - Disassemble PLAY.COM into a Microsoft M80-compatible
Z80 assembly source file (PLAY.MAC).

Produces source that reassembles to a byte-identical PLAY.COM with M80/L80.

M80 quirks the source must accommodate:
  - Symbols are SIGNIFICANT to about 6 characters; underscores are
    treated as terminators, so 'msg_present_voice1' collapses to 'msg'
    and collides with every other 'msg_*' label.  All labels here are
    short, alphanumeric, and unique in their first 6 characters.
  - Relative jumps (JR / DJNZ) require a SYMBOLIC operand for M80 to
    compute the offset.  Bare hex literals produce a 0 displacement and
    'R' errors.  This script auto-generates an Lnnnn label at every
    JR/JP/CALL/DJNZ target that doesn't already have a user label.
  - Externals to the CP/M zero page (BDOS, FCB, DMA, ...) must be
    declared with EQU; the disassembler emits an EQU block at the top.

Build (on the IMSAI):
    M80 =PLAY.MAC
    L80 PLAY,PLAY/N/E    ; produces PLAY.COM
"""

from collections import Counter
from z80dis import z80

from _paths import PLAY_COM, PROJECT_ROOT

PATH = str(PLAY_COM)
# Output a "raw" disassembly to project root so it doesn't clobber the
# hand-edited PLAYCDOS.MAC in New_CPM_Files/.  Diff manually if you re-run.
OUT  = str(PROJECT_ROOT / "PLAYCDOS_regenerated.MAC")
LOAD = 0x100

# Hand-curated data ranges (memory addresses, inclusive).
DATA_RANGES = [
    (0x02CD, 0x02D0, "init: scratch / divisor for decimal print"),
    (0x02D1, 0x02EE, "FCB for VOICES.MUS"),
    (0x02EF, 0x055A, "$-terminated message strings"),
    (0x055B, 0x0561, "static variables (VOFFS, SADDR, BFBAS, SVDSP)"),
    (0x0623, 0x067F, "duplicated/unreachable block"),
]

# CP/M zero-page externals: emitted as EQUates at the top of PLAY.MAC.
EXTERNALS = [
    ("WBOOT",  0x0000, "warm boot vector"),
    ("BDOS",   0x0005, "BDOS entry"),
    ("BDOSVC", 0x0006, "address word at BDOS+1 (top of TPA)"),
    ("FCB",    0x005C, "default FCB"),
    ("FCB1",   0x005D, "first byte of filename in default FCB"),
    ("DMA",    0x0080, "default DMA buffer"),
]

# User-named labels.  All <= 6 chars and unique within the first 6 chars.
# No underscores (M80 treats them as separators).
LABELS = {
    # Routines / code anchors
    0x0103: "MAIN",
    0x0135: "ASKSNG",
    0x013E: "OPNSNG",
    0x015B: "ASKPLP",
    0x016B: "REPLP",            # DJNZ target (PUSH BC inside repetition loop)
    0x0185: "EXITMS",
    0x018B: "ERRVOI",
    0x0190: "ERRNFD",
    0x0198: "PCHANG",
    0x022E: "PDTBYT",
    0x0264: "PDEMSG",
    0x0267: "PRMSG",
    0x026C: "RDCBUF",
    0x0279: "PCBUF",
    0x0286: "LDFILE",
    0x029B: "ASKYN",
    0x02AB: "PRDEC",
    0x02CD: "TDIG",
    0x02CE: "DIV10",
    0x02D1: "FCBVOI",
    0x02F0: "MBANR",
    0x0342: "MSONG",
    0x034E: "MAGAIN",
    0x0363: "MNEWS",
    0x036E: "MCHGPM",
    0x039E: "MREPQ",
    0x03B6: "MCHP1",
    0x03C6: "MCHP2",
    0x03D6: "MCHP3",
    0x03E6: "MCHP4",
    0x03F6: "MCHTMP",
    0x0406: "MPV1",
    0x0421: "MPV2",
    0x043D: "MPV3",
    0x0459: "MPV4",
    0x0475: "MNV1",
    0x048D: "MNV2",
    0x04A5: "MNV3",
    0x04BD: "MNV4",
    0x04D5: "MPRTMP",
    0x04F0: "MNTMP",
    0x0506: "MFNF",
    0x0517: "MSTLNG",
    0x0537: "MCLDVO",
    0x054B: "MBYE",
    0x055B: "VOFFS",
    0x055C: "SADDR",
    0x055E: "BFBAS",
    0x0560: "SVDSP",
    0x0562: "PLSNG",
    0x0579: "NXCMD",
    0x0584: "DSPCMD",
    0x05DA: "OUTITR",
    0x05DC: "INRLP",
    0x0623: "DEAD",
}

# Self-modifying-code patch points: addresses INSIDE other instructions
# (the immediate-operand bytes of LD B,n / LD DE,nn / LD H,n in the inner
# loop).  M80 won't let us put a 'LABEL:' declaration mid-instruction, so
# these are emitted as EQU directives at the top of the source instead.
EQUATES = [
    (0x05DB, "TMPIMM", "B-reload immediate inside LD B,n at OUTITR"),
    (0x05E0, "V1STIM", "Part 1 step immediate (LD DE,nn operand)"),
    (0x05E8, "V1PGIM", "Part 1 wavetable page immediate (LD H,n operand)"),
    (0x05EE, "V2STIM", "Part 2 step immediate"),
    (0x05F6, "V2PGIM", "Part 2 wavetable page immediate"),
    (0x05FE, "V3STIM", "Part 3 step immediate"),
    (0x0606, "V3PGIM", "Part 3 wavetable page immediate"),
    (0x060C, "V4STIM", "Part 4 step immediate"),
    (0x0614, "V4PGIM", "Part 4 wavetable page immediate"),
]

# Combined (externals + EQUates + labels) for operand resolution.
ALL_SYMBOLS = {addr: name for name, addr, _ in EXTERNALS}
for addr, name, _ in EQUATES:
    ALL_SYMBOLS[addr] = name
ALL_SYMBOLS.update(LABELS)


def in_data(addr):
    for s, e, descr in DATA_RANGES:
        if s <= addr <= e:
            return s, e, descr
    return None


def m80_hex(value, width=None):
    if width is None:
        width = 2 if value <= 0xFF else 4
    s = f"{value:0{width}X}H"
    if s[0].isalpha():
        s = "0" + s
    return s


def convert_operand(op_str):
    """Convert z80dis operand syntax to M80:
    - 0xNNNN -> label if known, else NNNNH form
    - lowercase condition codes (z, nz, c, nc) -> uppercase
    """
    import re

    def hex_repl(m):
        v = int(m.group(0), 16)
        if v in ALL_SYMBOLS:
            return ALL_SYMBOLS[v]
        return m80_hex(v)

    s = re.sub(r"0x[0-9a-fA-F]+", hex_repl, op_str)
    s = re.sub(
        r"\b(z|nz|c|nc|po|pe|p|m)\b(?=,)",
        lambda m: m.group(1).upper(),
        s,
    )
    return s


def find_branch_targets(data):
    """First pass: find every JR/DJNZ/JP/CALL target so we can ensure each
    has a label.  Returns the set of target addresses."""
    targets = set()
    i = 0
    while i < len(data):
        addr = LOAD + i
        if in_data(addr):
            _, e, _ = in_data(addr)
            i = (e - LOAD) + 1
            continue
        try:
            d = z80.decode(data[i:i + 4], addr)
            ln = d.len if 1 <= d.len <= 4 else 1
        except Exception:
            i += 1
            continue
        b = data[i]
        # Relative jumps (JR / DJNZ): 2 bytes, signed displacement
        if b in (0x18, 0x10, 0x20, 0x28, 0x30, 0x38) and ln == 2:
            disp = data[i + 1]
            if disp >= 128:
                disp -= 256
            tgt = (addr + 2 + disp) & 0xFFFF
            targets.add(tgt)
        # Absolute jumps / calls: 3 bytes, target in operand bytes
        elif b in (0xC3, 0xCD,
                   0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA,
                   0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC) and ln == 3:
            tgt = data[i + 1] | (data[i + 2] << 8)
            targets.add(tgt)
        i += ln
    return targets


def z80_opcode_census(data):
    counts = Counter()
    examples = {}

    def bump(key, addr, raw):
        counts[key] += 1
        if key not in examples:
            examples[key] = (addr, raw)

    i = 0
    while i < len(data):
        addr = LOAD + i
        rng = in_data(addr)
        if rng:
            _, e, _ = rng
            i = (e - LOAD) + 1
            continue

        try:
            d = z80.decode(data[i:i + 4], addr)
            ln = d.len if 1 <= d.len <= 4 else 1
        except Exception:
            ln = 1

        b = data[i]
        raw = bytes(data[i:i + ln])
        if b == 0xDD:
            bump("DD prefix (IX register operations)", addr, raw)
        elif b == 0xFD:
            bump("FD prefix (IY register operations)", addr, raw)
        elif b == 0xED:
            bump("ED prefix (LD (nn),rr / SBC HL,rr / etc.)", addr, raw)
        elif b == 0xCB:
            bump("CB prefix (BIT/SET/RES/RR/RL/SLA/SRA/SRL)", addr, raw)
        elif b == 0x18:
            bump("JR (unconditional relative jump)", addr, raw)
        elif b == 0x20:
            bump("JR NZ (relative)", addr, raw)
        elif b == 0x28:
            bump("JR Z (relative)", addr, raw)
        elif b == 0x30:
            bump("JR NC (relative)", addr, raw)
        elif b == 0x38:
            bump("JR C (relative)", addr, raw)
        elif b == 0x10:
            bump("DJNZ (decrement-and-jump-relative)", addr, raw)

        i += ln
    return counts, examples


def disasm():
    with open(PATH, "rb") as f:
        data = f.read()

    # First pass: find all branch targets.  Auto-generate Lnnnn labels for
    # any target that doesn't already have a user-facing name.
    targets = find_branch_targets(data)
    auto_labels = {}
    for tgt in targets:
        if LOAD <= tgt < LOAD + len(data) and tgt not in ALL_SYMBOLS:
            auto_labels[tgt] = f"L{tgt:04X}"
    ALL_SYMBOLS.update(auto_labels)
    LABELS.update(auto_labels)

    out = []
    w = out.append

    # Header + Z80 census
    w("; ============================================================")
    w("; PLAY.MAC -- Reassembled source for PLAY.COM")
    w(f"; Source binary: {PATH}")
    w(f"; Size: {len(data)} bytes (0{len(data):X}H), load address 100H")
    w("; Reassembles to byte-identical PLAY.COM with M80/L80.")
    w(";")
    w("; Z80-specific opcode census (proves Z80, not 8080):")
    counts, examples = z80_opcode_census(data)
    for mnem, n in counts.most_common():
        ex_addr, ex_bytes = examples[mnem]
        ex_str = " ".join(f"{b:02X}" for b in ex_bytes)
        w(f";   {n:4d}  {mnem:48s}  e.g. {ex_str:12s} @ 0{ex_addr:04X}H")
    w(";")
    w("; Build:")
    w(";   M80 =PLAY.MAC")
    w(";   L80 PLAY,PLAY/N/E         ; produces PLAY.COM")
    w("; ============================================================")
    w("")
    w("\t.Z80")
    w("\tASEG\t\t; absolute segment -- emit code at literal addresses")
    w("\t\t\t; (without this, M80 defaults to relocatable mode and L80")
    w("\t\t\t;  decides placement, breaking the hardcoded self-modifying-")
    w("\t\t\t;  code addresses in the inner loop.)")
    w("")
    w("; --- CP/M zero-page externals ---")
    for name, addr, descr in EXTERNALS:
        w(f"{name}\tEQU\t{m80_hex(addr, 4):<8s}\t; {descr}")
    w("")
    w("; --- Self-modifying-code patch points (operands inside INRLP) ---")
    for addr, name, descr in EQUATES:
        w(f"{name}\tEQU\t{m80_hex(addr, 4):<8s}\t; {descr}")
    w("")
    w("\tORG\t100H")
    w("")

    addr = LOAD
    end_addr = LOAD + len(data)
    while addr < end_addr:
        if addr in LABELS and addr != LOAD:
            w("")
            w(f"{LABELS[addr]}:")

        rng = in_data(addr)
        if rng:
            s, e, descr = rng
            if addr == s:
                w(f"; --- {descr} ---")
            row_end = min(addr + 16, e + 1, end_addr)
            for la in sorted(LABELS):
                if addr < la < row_end:
                    row_end = la
                    break
            chunk = data[addr - LOAD:row_end - LOAD]
            byte_strs = ", ".join(m80_hex(b, 2) for b in chunk)
            ascii_repr = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in chunk)
            w(f"\tDB\t{byte_strs:<60s}\t; {addr:04X}: {ascii_repr}")
            addr = row_end
            continue

        try:
            d = z80.decode(data[addr - LOAD:addr - LOAD + 4], addr)
            ln = d.len if 1 <= d.len <= 4 else 1
            mnem = z80.disasm(data[addr - LOAD:addr - LOAD + ln], addr)
        except Exception:
            ln = 1
            mnem = None

        if mnem is None or ln == 0:
            b = data[addr - LOAD]
            w(f"\tDB\t{m80_hex(b, 2):<8s}\t\t; {addr:04X}: ?? raw byte")
            addr += 1
            continue

        m80_mnem = convert_operand(mnem)
        bytes_str = " ".join(f"{b:02X}" for b in data[addr - LOAD:addr - LOAD + ln])
        w(f"\t{m80_mnem:<28s}\t; {addr:04X}: {bytes_str}")
        addr += ln

    w("")
    w("\tEND\t100H\t\t; entry point for the loaded COM file")
    w("")

    with open(OUT, "w", newline="\n", encoding="ascii", errors="replace") as f:
        f.write("\n".join(out))

    print(f"wrote {OUT}: {len(out)} lines")
    print(f"auto-generated labels: {len(auto_labels)}")
    print()
    print("Z80-specific opcode summary:")
    for mnem, n in counts.most_common():
        print(f"  {n:4d}  {mnem}")


if __name__ == "__main__":
    disasm()
