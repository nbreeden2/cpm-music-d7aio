========================================================================
J.S. BACH -- TWO-PART INVENTIONS, BWV 772 - 786
========================================================================

THE MUSIC
---------
On this disk you will find Bach's fifteen Two-Part
Inventions (BWV 772 - 786), composed in Coethen around
1720-1723 and revised in Leipzig in 1723.  Bach wrote
them as teaching pieces for his eldest son Wilhelm
Friedemann and for his own keyboard students -- the
autograph fair copy is titled "Aufrichtige Anleitung"
(Honest Instruction) and is explicit that the player
should learn to "obtain a cantabile manner of playing
and at the same time acquire a strong foretaste of
composition".  Two strict, equally singing voices in
invertible counterpoint, one short piece per major and
minor key in the order C, c, D, d, E-flat, E, e, F, f,
G, g, A, a, B-flat, b.

On a four-voice wavetable engine, the two written voices
are each doubled by a second voice playing the same line
with a different timbre -- the same arrangement used on
the original Cromemco-era BACH .MUS files.

FILES ON THIS DISK
------------------
  PLAYZ80.COM    The player program
  VOICES.MUS     Original 6-slot Cromemco wavetable bank
  BACH1.MUS      Invention No.  1 in C   major  (BWV 772)
  BACH2.MUS      Invention No.  2 in C   minor  (BWV 773)
  BACH3.MUS      Invention No.  3 in D   major  (BWV 774)
  BACH4.MUS      Invention No.  4 in D   minor  (BWV 775)
  BACH5.MUS      Invention No.  5 in Eb  major  (BWV 776)
  BACH6.MUS      Invention No.  6 in E   major  (BWV 777)
  BACH7.MUS      Invention No.  7 in E   minor  (BWV 778)
  BACH8.MUS      Invention No.  8 in F   major  (BWV 779)
  BACH9.MUS      Invention No.  9 in F   minor  (BWV 780)
  BACH10.MUS     Invention No. 10 in G   major  (BWV 781)
  BACH11.MUS     Invention No. 11 in G   minor  (BWV 782)
  BACH12.MUS     Invention No. 12 in A   major  (BWV 783)
  BACH13.MUS     Invention No. 13 in A   minor  (BWV 784)
  BACH14.MUS     Invention No. 14 in Bb  major  (BWV 785)
  BACH15.MUS     Invention No. 15 in B   minor  (BWV 786)
  INVENT.QSB     QPM SUBMIT batch -- plays all 15 in order

To hear one piece:        A>PLAYZ80 BACH1.MUS
One pass with no prompts: A>PLAYZ80 BACH1.MUS /Q
Play all 15 in order:     A>SUBMIT INVENT

MIDI SOURCE
-----------
The score data was taken from Standard MIDI Files downloaded
from the Bach Central MIDI archive:
  https://www.bachcentral.com/midiindexcomplete.html

CONVERSION PROCESS
------------------
Mode '2' (invention) of midi2mus.py was used.  This mode
reads two monophonic MIDI voice tracks and routes each
onto a pair of physical voices: track 1 onto Voice 1
(sine) plus Voice 3 (skewed saw) at the written pitch;
track 2 onto Voice 2 (even-harmonic, octave up) plus
Voice 4 (octave-shifter, octave up).  The result is two
written lines, each fattened by a doubling voice in a
different timbre, occupying all four parallel oscillators.
This is the same encoding strategy used by the original
Cromemco-era BACH .MUS files.

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
  D:/CPMEMU/disks/BachInvent.unpacked/
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