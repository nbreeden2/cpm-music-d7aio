========================================================================
J.S. BACH -- SUITE No. 4 IN Eb MAJOR, BWV 1010  (SOLO CELLO)
========================================================================

THE MUSIC
---------
On this disk you will find the six movements of Bach's
fourth unaccompanied Cello Suite (BWV 1010, in E-flat
major), composed around 1717-1723 at the court of
Anhalt-Coethen.  The fourth suite is considered the most
technically demanding of the first four: the flat key sits
awkwardly on a cello's open-string resonances, and the
Prelude's relentless broken arpeggios test the player's
string-crossing technique.  The "galanteries" pair here
are Bourrees rather than the Minuets of Suite 1.

The cello plays mostly one voice with brief double-stops,
so the same conversion strategy as Suite 1 is used.  The
disk name "BachCello2-Eb" reflects that this is the second
cello-suite disk to be made, not that this is Cello Suite
No. 2 -- this is Suite No. 4.

FILES ON THIS DISK
------------------
  PLAYZ80.COM    The player program
  VOICES.MUS     Wavetable bank (slot 2 = custom cello)
  PRELUDE.MUS    Movement 1 -- Prelude
  ALLEMAND.MUS   Movement 2 -- Allemande
  COURANTE.MUS   Movement 3 -- Courante
  SARABAND.MUS   Movement 4 -- Sarabande
  BOURREE.MUS    Movement 5 -- Bourree I / II
  GIGUE.MUS      Movement 6 -- Gigue
  CELLO.SUB      SUBMIT batch -- plays all six in order
  CELLO.QSB      QPM copy of CELLO.SUB

To hear one movement:           A>PLAYZ80 PRELUDE.MUS
One pass with no prompts:       A>PLAYZ80 PRELUDE.MUS /Q
Play the whole suite in order:  A>SUBMIT CELLO

MIDI SOURCE
-----------
The score data was taken from Standard MIDI Files downloaded
from the Bach Central MIDI archive:
  https://www.bachcentral.com/midiindexcomplete.html

CONVERSION PROCESS
------------------
Mode '1' (solo) of midi2mus.py was used: it reads the
single voice track of the MIDI source and allocates each
cell to Voice 1 (low note, sine), Voice 2 (middle note,
only when three notes sound), and Voice 3 (high note,
cello timbre).  Voice 4 is silent.  The VOICES.MUS bank
on this disk has a synthetic cello waveform in slot 2 --
an additive sawtooth series with a Gaussian formant at
the third harmonic and a 4th-order low-pass at the 7th.
Slots 0, 1, 3, 4, 5 are byte-identical to the original
Cromemco bank.

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
  D:/CPMEMU/disks/BachCello2-Eb.unpacked/
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