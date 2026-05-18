# The Well-Tempered Clavier, Book I — 4-voice fugues

J.S. Bach, BWV 846–893 (Book I = BWV 846–869).  This disk holds the
eight 4-voice fugues from Book I that converted cleanly with
`midi2mus.py --voices 4`.  Each fugue is one `.MUS` file;
[`WTCBKI.SUB`](WTCBKI.SUB) plays them back-to-back via PLAYZ80's
`/Q` (quiet) switch.

## Pieces on this disk

| File | BWV | Key |
|---|---|---|
| `FUGUE1.MUS`  | 846 | C major |
| `FUGUE5.MUS`  | 850 | D major |
| `FUGUE14.MUS` | 859 | F♯ minor |
| `FUGUE16.MUS` | 861 | G minor |
| `FUGUE17.MUS` | 862 | A♭ major |
| `FUGUE18.MUS` | 863 | G♯ minor |
| `FUGUE20.MUS` | 865 | A minor |
| `FUGUE23.MUS` | 868 | B major |

The other Book I fugues from this MIDI corpus were skipped because they
are 2-voice (fugue 10), 3-voice (fugues 2, 3, 7, 9, 19, 21), 5-voice
(fugues 4, 22), or because the source `.mid` is corrupt and can't be
parsed (fugues 6, 8, 11, 12, 13, 15, 19, 24, preludes 1, 2).

## Files on this disk

| File | Source | Notes |
|---|---|---|
| `fugue*.mid` | original MIDI sources (kept for re-conversion) | not used on the CP/M side |
| `FUGUE*.MUS` | converted via `midi2mus.py --voices 4` | eight fugues |
| `WTCBKI.SUB` | hand-written | SUBMIT batch: plays all eight in BWV order with `/Q` |
| `VOICES.MUS` | byte-identical copy of `Original_CPM_Files/VOICES.MUS` | original CDOS 6-slot bank; no custom voices |
| `*_sim.wav` | rendered by `Scripts/simulate.py` against the original `VOICES.MUS` | preview files; do not need to be uploaded to CP/M |

## VOICES.MUS

This disk uses the **original CDOS `VOICES.MUS` bank verbatim**.
`midi2mus.py --voices 4` defaults to timbres `(0, 2, 4, 0)` =
sine / saw / square / sine — three of the six standard slots, all of
which play at the written pitch (no octave-shifting timbres).  So no
custom bank is needed; the file in this folder is byte-identical to
`Original_CPM_Files/VOICES.MUS`.

If you want to swap in a different timbre on, say, V1, use the
`--timbres` flag on midi2mus.py; you do not need to change
`VOICES.MUS` itself unless you want a wavetable that isn't already in
the original bank.

## Regenerating

```
# re-convert one fugue (substitute the BWV-relative fugue number)
python Scripts/midi2mus.py MIDI/WellTemperedClavierBookOne_FourVoiceFugues/fugue1.mid \
       MIDI/WellTemperedClavierBookOne_FourVoiceFugues/FUGUE1.MUS --voices 4

# preview against the bundled VOICES.MUS
python Scripts/simulate.py MIDI/WellTemperedClavierBookOne_FourVoiceFugues/FUGUE1.MUS \
       --voices MIDI/WellTemperedClavierBookOne_FourVoiceFugues/VOICES.MUS \
       -o MIDI/WellTemperedClavierBookOne_FourVoiceFugues/FUGUE1_sim.wav
```

The matching CP/M-side disk image is committed in
[`Disks/BachWTC1-4v.unpacked/`](../../Disks/BachWTC1-4v.unpacked/) (host-side
folder tree) and [`Disks/BachWTC1-4v.dsk`](../../Disks/BachWTC1-4v.dsk)
(packed 256-sector floppy image for fdcServer / Z80Pack).  Both
forms carry `PLAYZ80.COM`, `VOICES.MUS`, the eight `FUGUE*.MUS`
files, `WTCBKI.SUB` / `WTCBKI.QSB`, and a CP/M-shaped `README.TXT`.
A live working copy of the unpacked tree also lives at
`D:/CPMEMU/disks/BachWTC1-4v.unpacked/0/` for fdcServer to mount;
`Scripts/_gen_disk_readme.py` writes the per-disk `README.TXT` to
both locations so they stay in sync.

See the project root [`README.md`](../../README.md) for the `.MUS`
format, the 4-voice-mode design, and the calibration that ties the
.MUS files to 11,169 Hz hardware.  See [`Scripts/README.md`](../../Scripts/README.md)
for the per-script reference.
