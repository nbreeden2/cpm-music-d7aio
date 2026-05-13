# Tetris (Korobeiniki) arrangements

Chiptune-style transcriptions of the Tetris main theme for the 4-voice
CP/M wavetable player.  Three movements; `TETRIS.SUB` plays them
back-to-back via PLAYZ80's `/Q` (quiet) switch.

## Files on this disk

| File | Source | Notes |
|---|---|---|
| `*.mid` | various MIDI sources online | dropped in for conversion |
| `TETRIS.MUS` | `Tetris - Tetris Main Theme.mid` via `--voices 1 --timbres 2,2,2,0` | single-channel main theme, polyphony 3 |
| `GBFUTUR.MUS` | `Game_System__Gameboy_Tetris_Music_A_Futuristic_Remix.mid` via `--voices 1 --merge --timbres 2,2,2,0` | drum-stripped multi-track Game Boy "Futuristic" remix |
| `NESMETAL.MUS` | `Game_System__Nintendo_Tetris_Music_C_Metal_Remix.mid` via `--voices 1 --merge --timbres 2,2,2,0` | NES Music C "Metal" remix (no drums in source) |
| `TETRIS.SUB` | hand-written + CPMFMT'd | SUBMIT batch: plays all three in order with `/Q` |
| **`VOICES.MUS`** | **custom (NOT the original CDOS bank)** | see below |
| `*_sim.wav` | rendered by `Scripts/simulate.py --voices VOICES.MUS` | preview files; do not need to be uploaded to CP/M |
| `triangle_A4.wav` | rendered by `build_voices.py --audition triangle` | 3-second A4 reference for the triangle voice in slot 2 |
| `pulse25_A4.wav` | same | 25%-duty pulse reference (not used in the current arrangements, kept for future tweaks) |

## Source files NOT converted

The following MIDIs are in the folder for reference but were not
converted -- their polyphony exceeds what the 4-voice engine can
represent without unacceptable note loss in the reducer:

| File | Polyphony | Reason |
|---|---|---|
| `Game_System__Gameboy_Tetris_Music_A_Classical_RemixSequenced_by__ErSerAs.mid` | 8 | dense arrangement |
| `Game_System__Super_Nintendo_Tetris_2_Music_Asequenced_by_.mid` | 9 | dense, drum-heavy |
| `Tetris2.mid` | 9 | dense, drum-heavy |
| `tetris.mid` | 11 | dense, drum-heavy |
| `Russian_Folk_Song__Korobochka_aka_Tetris.mid` | 14 | extreme orchestration (11 MIDI channels) |

A future converter pass with smarter channel-selection / "render top-N
most-prominent voices" tooling could revisit these.

## Custom `VOICES.MUS`

The `VOICES.MUS` in this folder is **not** the original CDOS bank.
Slot 2 has been replaced with `triangle`, a synthetic triangle wave
(linear ramp: zero -> +60 -> 0 -> -60 -> ~0).  Slots 0 / 1 / 3 / 4 / 5
are byte-identical to the original.

The triangle voice was added because pure-square chiptune (timbre 4)
sounded too buzzy on this engine when used on all three active
voices.  Triangle has the same odd-harmonic content as square but
the amplitudes fall as `1/n^2` instead of `1/n`, so it's noticeably
softer / less edgy while still carrying clear pitched content --
matching the NES / Game Boy "triangle channel" role.

The file is still exactly 1536 bytes (6 x 256) so PLAY.COM /
PLAYCDOS / PLAYZ80 load it unchanged.  As with the cello-suite disks,
this is a self-contained per-disk override -- the Bach / sinfonia /
cello disks keep using their own banks and are unaffected.

### Timbre routing

All three movements use `--timbres 2,2,2,0` in mode `1`:

| Voice | Role | Slot |
|---|---|---|
| V1 | bass (low note in chord cells; doubles V3 in monophonic cells) | slot 2 = triangle |
| V2 | chord middle (only active in 3-note cells) | slot 2 = triangle |
| V3 | melody (high note in chord cells) | slot 2 = triangle |
| V4 | always silent | slot 0 = sine (safe-zero: wavetable[sine][0]=0) |

### Regenerating

```
# rebuild the Tetris bank
python Scripts/build_voices.py --replace 2=triangle \
       -o MIDI/TETRIS/VOICES.MUS

# convert (single-track source)
python Scripts/midi2mus.py "MIDI/TETRIS/Tetris - Tetris Main Theme.mid" \
       MIDI/TETRIS/TETRIS.MUS --voices 1 --timbres 2,2,2,0

# convert (multi-track source with drums stripped)
python Scripts/midi2mus.py \
       "MIDI/TETRIS/Game_System__Gameboy_Tetris_Music_A_Futuristic_Remix.mid" \
       MIDI/TETRIS/GBFUTUR.MUS --voices 1 --merge --timbres 2,2,2,0

# preview
python Scripts/simulate.py MIDI/TETRIS/GBFUTUR.MUS \
       --voices MIDI/TETRIS/VOICES.MUS \
       -o MIDI/TETRIS/GBFUTUR_sim.wav
```

See the project root [`README.md`](../../README.md) section 5.1 for
more background on the custom-`VOICES.MUS`-per-disk pattern, and
[`Scripts/README.md`](../../Scripts/README.md) for the per-script
reference (including `--timbres` and `--merge`).
