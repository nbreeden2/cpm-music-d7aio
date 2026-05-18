========================================================================
J.S. BACH -- THREE-PART SINFONIAS, BWV 787 - 801
========================================================================

THE MUSIC
---------
On this disk you will find Bach's fifteen Three-Part
Inventions, which he called "Sinfonias" (BWV 787 - 801),
composed at Coethen around 1723.  They form the companion
set to the Two-Part Inventions and follow the same key
order (C, c, D, d, E-flat, E, e, F, f, G, g, A, a, B-flat,
b).  Three strict equal voices in invertible counterpoint,
with notably more chromatic and harmonic ambition than the
two-part set -- the F-minor sinfonia (No. 9) is, in its
mere twenty-nine measures, one of Bach's most haunting
chromatic miniatures.

This is the "faithful" three-voice arrangement.  Each of
the three written voices is played by exactly one of the
player's four voices at the written pitch; the fourth
voice is silent.  A companion disk (BachSinfoniaAlt) plays
the same music with the soprano line octave-doubled.

FILES ON THIS DISK
------------------
  PLAYZ80.COM     The player program
  VOICES.MUS      Original 6-slot Cromemco wavetable bank
  SINFON1.MUS     Sinfonia No.  1 in C   major  (BWV 787)
  SINFON2.MUS     Sinfonia No.  2 in C   minor  (BWV 788)
  SINFON3.MUS     Sinfonia No.  3 in D   major  (BWV 789)
  SINFON4.MUS     Sinfonia No.  4 in D   minor  (BWV 790)
  SINFON5.MUS     Sinfonia No.  5 in Eb  major  (BWV 791)
  SINFON6.MUS     Sinfonia No.  6 in E   major  (BWV 792)
  SINFON7.MUS     Sinfonia No.  7 in E   minor  (BWV 793)
  SINFON8.MUS     Sinfonia No.  8 in F   major  (BWV 794)
  SINFON9.MUS     Sinfonia No.  9 in F   minor  (BWV 795)
  SINFON10.MUS    Sinfonia No. 10 in G   major  (BWV 796)
  SINFON11.MUS    Sinfonia No. 11 in G   minor  (BWV 797)
  SINFON12.MUS    Sinfonia No. 12 in A   major  (BWV 798)
  SINFON13.MUS    Sinfonia No. 13 in A   minor  (BWV 799)
  SINFON14.MUS    Sinfonia No. 14 in Bb  major  (BWV 800)
  SINFON15.MUS    Sinfonia No. 15 in B   minor  (BWV 801)
  SINFONIA.QSB    QPM SUBMIT batch -- plays all 15 in order

To hear one piece:        A>PLAYZ80 SINFON1.MUS
One pass with no prompts: A>PLAYZ80 SINFON1.MUS /Q
Play all 15 in order:     A>SUBMIT SINFONIA

MIDI SOURCE
-----------
The score data was taken from Standard MIDI Files downloaded
from the Bach Central MIDI archive:
  https://www.bachcentral.com/midiindexcomplete.html

CONVERSION PROCESS
------------------
Mode '3' (sinfonia faithful) of midi2mus.py was used.
Each of the three monophonic MIDI voice tracks is routed
onto one physical voice: soprano on Voice 1 (sine), alto
on Voice 2 (even-harmonic at the written pitch, sounding
an octave higher per the wavetable shape), tenor / bass
on Voice 3 (skewed saw at the written pitch).  Voice 4
is silent, its timbre forced to sine so the wavetable
DC offset on the second DAC channel is minimized.

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
  D:/CPMEMU/disks/BachSinfonia.unpacked/
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