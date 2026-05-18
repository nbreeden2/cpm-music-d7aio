========================================================================
J.S. BACH -- WELL-TEMPERED CLAVIER, BOOK II  (PRELUDES & FUGUES)
========================================================================

THE MUSIC
---------
On this disk you will find twenty-one preludes and fugues
from Bach's Das Wohltemperierte Klavier, Buch II (The
Well-Tempered Clavier, Book II), BWV 870 - 893, completed
in Leipzig in 1742, twenty years after Book I.  The full
Book II again pairs a Prelude with a Fugue in each of the
twelve major and twelve minor keys in ascending chromatic
order from C major.  This disk holds the nine prelude-and-
fugue pairs whose MIDI sources parse cleanly (BWV 870 -
878), plus three more fugues from later in the book whose
companion preludes were corrupt in the source corpus
(FUGUE10, FUGUE11, FUGUE12 from BWV 879, 880, 881).

The Book II MIDI sources are "single-track polyphonic
exports" -- all notes from all voices share one MIDI
track rather than living on separate tracks per voice.
That means the converter can't route written voices onto
individual physical voices the way it does for Book I;
instead it uses the polyphony reducer to fit up to three
simultaneous notes per cell across Voices 1, 2, and 3,
dropping shorter ornament notes when more than three
voices sound at once.  Voice 4 is silent.  Dense moments
in the 4-voice fugues lose one of the four lines as a
result; the lighter preludes mostly come through intact.

FILES ON THIS DISK
------------------
  PLAYZ80.COM     The player program
  VOICES.MUS      Original 6-slot Cromemco wavetable bank
  PRELUDE1.MUS    Prelude  I    in C   major   (BWV 870)
  FUGUE1.MUS      Fugue    I    in C   major   (BWV 870)
  PRELUDE2.MUS    Prelude  II   in C   minor   (BWV 871)
  FUGUE2.MUS      Fugue    II   in C   minor   (BWV 871)
  PRELUDE3.MUS    Prelude  III  in C#  major   (BWV 872)
  FUGUE3.MUS      Fugue    III  in C#  major   (BWV 872)
  PRELUDE4.MUS    Prelude  IV   in C#  minor   (BWV 873)
  FUGUE4.MUS      Fugue    IV   in C#  minor   (BWV 873)
  PRELUDE5.MUS    Prelude  V    in D   major   (BWV 874)
  FUGUE5.MUS      Fugue    V    in D   major   (BWV 874)
  PRELUDE6.MUS    Prelude  VI   in D   minor   (BWV 875)
  FUGUE6.MUS      Fugue    VI   in D   minor   (BWV 875)
  PRELUDE7.MUS    Prelude  VII  in Eb  major   (BWV 876)
  FUGUE7.MUS      Fugue    VII  in Eb  major   (BWV 876)
  PRELUDE8.MUS    Prelude  VIII in D#  minor   (BWV 877)
  FUGUE8.MUS      Fugue    VIII in D#  minor   (BWV 877)
  PRELUDE9.MUS    Prelude  IX   in E   major   (BWV 878)
  FUGUE9.MUS      Fugue    IX   in E   major   (BWV 878)
  FUGUE10.MUS     Fugue    X    in E   minor   (BWV 879)
  FUGUE11.MUS     Fugue    XI   in F   major   (BWV 880)
  FUGUE12.MUS     Fugue    XII  in F   minor   (BWV 881)
  WTCBKII.SUB     SUBMIT batch -- plays all 21 in pair order
  WTCBKII.QSB     QPM copy of WTCBKII.SUB

To hear one piece:        A>PLAYZ80 PRELUDE1.MUS
One pass with no prompts: A>PLAYZ80 PRELUDE1.MUS /Q
Play all 21 in order:     A>SUBMIT WTCBKII

MIDI SOURCE
-----------
The score data was taken from Standard MIDI Files downloaded
from the Bach Central MIDI archive:
  https://www.bachcentral.com/midiindexcomplete.html

CONVERSION PROCESS
------------------
Mode '1' (solo with polyphony reducer) of midi2mus.py was
used with the --merge flag.  --merge tells the converter
to read notes from every MIDI track in the source file
(the Book II MIDIs are single-track polyphonic exports,
so all notes live on track 1 rather than being split into
voice-per-track).  The reducer scores each candidate note
in a cell by cell-coverage * total-note-duration and
keeps up to three -- low note onto Voice 1 (sine), middle
onto Voice 2 (sine, only when three sound at once), high
onto Voice 3 (skewed saw).  Voice 4 is silent.  In dense
4-voice cells one voice is dropped per cell, with the
scoring biased so that sustained structural lines survive
and short trill / mordent ornaments lose out.

THE PLAYER PROGRAM
------------------
PLAYZ80 is a 4-voice wavetable synthesizer for the Cromemco
D+7AIO analog interface card.  Each voice ("Part 1..4") sweeps
a 16-bit phase accumulator through a 256-byte single-cycle
wavetable selected from VOICES.MUS.  Pairs of voices sum in
software and write their 8-bit signed sum to two of the D+7AIO's
analog output channels:

  Port 19h (channel 1, AN1)   Voices 1 + 2 summed
  Port 1Bh (channel 3, AN3)   Voices 3 + 4 summed

These are the D+7AIO's default port assignments -- the card's
base address is 18h and the two channels at 19h / 1Bh are AN1
and AN3.  The other five channels (1Dh, 1Fh, plus analog inputs)
are unused by the player.  No real-time MIDI, no envelopes, no
portamento -- just four parallel oscillators reading from one of
six pre-baked wavetables, plus a tempo knob.  On a 4 MHz Z80 the
player runs at a calibrated sample rate of about 11169 Hz.

PASSIVE MIXER (D+7AIO -> SPEAKER)
---------------------------------
The two D+7AIO analog outputs share a single mono speaker line
through a passive summer + RC low-pass filter:

  DAC1 (port 19h) -----[ R1 = 10K ohm ]-----+
                                            |
                                            +--- Audio Out --- speaker
                                            |
  DAC2 (port 1Bh) -----[ R2 = 10K ohm ]-----+
                                            |
                                      [ C1 = 10 nF ]
                                            |
                                            v
                                        Analog GND
                                        (D+7AIO ref)

R1 and R2 form a passive voltage summer; the junction sees
(DAC1 + DAC2) / 2 with R1 || R2 = 5K source impedance.  C1
forms a reconstruction low-pass filter with corner ~3.2 kHz,
which sits below the player's Nyquist (~5.58 kHz) and smooths
the DAC staircase.  The reference must be the D+7AIO's analog
ground, not the S-100 digital ground -- the card brings them
out separately to keep DAC switching noise off the audio.

DISK FORMAT (.unpacked)
-----------------------
On the host PC, this disk is the folder
  D:/CPMEMU/disks/BachWTC2.unpacked/
with one numbered subfolder per CP/M USER area (0/ = USER 0,
the default; 1/ = USER 1, etc.).  All of the .MUS files, the
player .COM, and this README live in subfolder 0/.  The
fdcServer process watches the folder and serves it to cpmemu
(over TCP) or to a real IMSAI 8080 (over RS-232).  Edit a file
on the host and CP/M sees the change the next time it reads.
fdcServer also manages two hidden files at the disk root
($BOOT and $ATTR) -- do not edit those by hand.

fdcServer documentation:
  https://thehighnibble.com/sdh100/fdc-server/#table-of-contents

PROJECT REPOSITORY
------------------
Source code for the player (PLAYZ80, PLAY8080, PLAYCDOS), the
MIDI-to-MUS converter (midi2mus.py), the wavetable analysis
scripts, and all of the disk images on this system:
  https://github.com/nbreeden2/cpm-music-d7aio

------------------------------------------------------------------------
Neil Breeden   <retrotechreboot@gmail.com>
