# Die Kunst der Fuge — 4-voice movements

J.S. Bach, BWV 1080 (1742–1750).  This disk holds the twelve 4-voice
movements of *The Art of Fugue* — all the contrapuncti, the regular
fugues, the counter-fugues, the inversions, one half of the mirror
fugue, the triple fugue, and the unfinished quadruple fugue that
Bach left at his death.  Each movement is one `.MUS` file;
[`AOF.SUB`](AOF.SUB) plays them in performance order via PLAYZ80's
`/Q` (quiet) switch.

## Pieces on this disk

The Contrapuncti are numbered as in Bach's autograph manuscript.
Source-file basenames in the MIDI corpus are abbreviated; the
mapping is shown below.

| Source `.mid` | CP/M file | Movement |
|---|---|---|
| `cnt1.mid`   | `CNT1.MUS`   | Contrapunctus 1 — simple fugue on the main subject |
| `cnt2.mid`   | `CNT2.MUS`   | Contrapunctus 2 — simple fugue, dotted-rhythm variant of the subject |
| `cnt3.mid`   | `CNT3.MUS`   | Contrapunctus 3 — simple fugue on the inverted subject |
| `reg1.mid`   | `REG1.MUS`   | Contrapunctus 4 — simple fugue on the inverted subject (regular fugue) |
| `reg2.mid`   | `REG2.MUS`   | Contrapunctus 9 — double fugue at the twelfth (regular fugue) |
| `dou1.mid`   | `DOU1.MUS`   | Contrapunctus 5 — counter-fugue (subject vs. inversion) |
| `dou2.mid`   | `DOU2.MUS`   | Contrapunctus 6 — counter-fugue *in stylo francese*, diminution |
| `inver1.mid` | `INVER1.MUS` | Contrapunctus 7 *per augmentationem et diminutionem* |
| `inver2.mid` | `INVER2.MUS` | Contrapunctus 10 — double fugue at the tenth |
| `mir1.mid`   | `MIR1.MUS`   | Contrapunctus 12 *rectus* — mirror fugue (one half) |
| `tri2.mid`   | `TRI2.MUS`   | Contrapunctus 11 — triple fugue |
| `unfin.mid`  | `UNFIN.MUS`  | Contrapunctus 14 — the unfinished quadruple fugue (B-A-C-H subject) |

The 2-voice canons (`can1.mid`–`can4.mid`), the 3-voice
Contrapunctus 12 *inversus* (`mir2.mid`) and the 3-voice
Contrapunctus 13 *rectus* (`tri1.mid`) live on a separate disk —
they need `midi2mus.py --voices 2` or `--voices 3` respectively.

## Files on this disk

| File | Source | Notes |
|---|---|---|
| `*.mid` | original MIDI sources (kept for re-conversion) | not used on the CP/M side |
| `*.MUS` | converted via `midi2mus.py --voices 4` | twelve movements |
| `AOF.SUB` | hand-written | SUBMIT batch: plays all twelve in performance order with `/Q` |
| `VOICES.MUS` | byte-identical copy of `Original_CPM_Files/VOICES.MUS` | original CDOS 6-slot bank; no custom voices |
| `*_sim.wav` | rendered by `Scripts/simulate.py` against the original `VOICES.MUS` | preview files; do not need to be uploaded to CP/M |

## VOICES.MUS

This disk uses the **original CDOS `VOICES.MUS` bank verbatim**.
`midi2mus.py --voices 4` defaults to timbres `(0, 2, 4, 0)` =
sine / saw / square / sine, which are three of the six standard slots
and all play at the written pitch (no octave-shifting timbres).  So no
custom bank is needed; the file in this folder is byte-identical to
`Original_CPM_Files/VOICES.MUS`.

If you want a different timbre on any voice, use `--timbres` on
midi2mus.py; you do not need to change `VOICES.MUS` itself unless you
want a wavetable that isn't already in the original bank.

## Regenerating

```
# re-convert one movement
python Scripts/midi2mus.py MIDI/ArtOfFugue_FourVoicePieces/cnt1.mid \
       MIDI/ArtOfFugue_FourVoicePieces/CNT1.MUS --voices 4

# preview against the bundled VOICES.MUS
python Scripts/simulate.py MIDI/ArtOfFugue_FourVoicePieces/CNT1.MUS \
       --voices MIDI/ArtOfFugue_FourVoicePieces/VOICES.MUS \
       -o MIDI/ArtOfFugue_FourVoicePieces/CNT1_sim.wav
```

The matching CP/M-side `.unpacked` disk image lives at
`D:/CPMEMU/disks/BachAOF-4v.unpacked/0/` and carries `PLAYZ80.COM`,
`VOICES.MUS`, the twelve `.MUS` files, and `AOF.SUB`.

See the project root [`README.md`](../../README.md) for the `.MUS`
format, the 4-voice-mode design, and the calibration that ties the
.MUS files to 11,169 Hz hardware.  See [`Scripts/README.md`](../../Scripts/README.md)
for the per-script reference.
