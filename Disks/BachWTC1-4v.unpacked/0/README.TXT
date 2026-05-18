========================================================================
J.S. BACH -- WELL-TEMPERED CLAVIER, BOOK I  (4-VOICE FUGUES)
========================================================================

THE MUSIC
---------
On this disk you will find eight of the four-voice fugues
from Bach's Das Wohltemperierte Klavier, Buch I (The
Well-Tempered Clavier, Book I), BWV 846 - 869, completed
in Coethen in 1722.  Book I pairs a Prelude with a Fugue
in each of the twelve major and twelve minor keys, in
ascending chromatic order from C major; this disk holds
only the fugues, and only the eight that are written in
strict four-part counterpoint and whose MIDI sources in
this corpus parse cleanly.

The 4-voice fugues here are some of the most architect-
urally ambitious in the set: the dense C-major opening
of fugue I, the chromatic anguish of fugue XIV in F-sharp
minor, the dancing G minor of fugue XVI, the great A
minor of fugue XX with its augmentation and stretto
climax.  Each line plays at its written pitch on one of
the four voices, summing acoustically at the speaker.

FILES ON THIS DISK
------------------
  PLAYZ80.COM    The player program
  VOICES.MUS     Original 6-slot Cromemco wavetable bank
  FUGUE1.MUS     Fugue I   in C  major     (BWV 846)
  FUGUE5.MUS     Fugue V   in D  major     (BWV 850)
  FUGUE14.MUS    Fugue XIV in F# minor     (BWV 859)
  FUGUE16.MUS    Fugue XVI in G  minor     (BWV 861)
  FUGUE17.MUS    Fugue XVII in Ab major    (BWV 862)
  FUGUE18.MUS    Fugue XVIII in G# minor   (BWV 863)
  FUGUE20.MUS    Fugue XX  in A  minor     (BWV 865)
  FUGUE23.MUS    Fugue XXIII in B  major   (BWV 868)
  WTCBKI.SUB     SUBMIT batch -- plays all 8 in BWV order
  WTCBKI.QSB     QPM copy of WTCBKI.SUB

To hear one fugue:        A>PLAYZ80 FUGUE1.MUS
One pass with no prompts: A>PLAYZ80 FUGUE1.MUS /Q
Play all 8 in order:      A>SUBMIT WTCBKI

MIDI SOURCE
-----------
The score data was taken from Standard MIDI Files downloaded
from the Bach Central MIDI archive:
  https://www.bachcentral.com/midiindexcomplete.html

CONVERSION PROCESS
------------------
Mode '4' (SATB chorale / 4-voice fugue) of midi2mus.py
was used.  Each of the four monophonic MIDI voice tracks
is routed one-to-one onto a physical voice at its written
pitch -- soprano on Voice 1 (sine), alto on Voice 2
(skewed saw), tenor on Voice 3 (square), bass on Voice 4
(sine).  None of the voices uses an octave-shifting
timbre, so what you hear matches the score.  This mode
was added to the converter specifically for this disk
and for the Art of Fugue disk.

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
  D:/CPMEMU/disks/BachWTC1-4v.unpacked/
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