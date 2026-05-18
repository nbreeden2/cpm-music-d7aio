========================================================================
J.S. BACH -- DIE KUNST DER FUGE, BWV 1080  (4-VOICE)
========================================================================

THE MUSIC
---------
On this disk you will find the twelve four-voice movements
of Bach's Die Kunst der Fuge (The Art of Fugue, BWV 1080),
his last major work, written from about 1742 until his
death in 1750.  All twenty contrapuncti of the original
collection are built on the same D-minor subject; this
disk holds the twelve that are written for four voices --
the simple fugues, counter-fugues, double fugues, fugues
on the inverted subject, one half of the mirror fugue, the
triple fugue, and the unfinished quadruple fugue that
breaks off mid-bar at the point where Bach is said to
have died.

Bach left no specification of which instrument should
play the work, so it has been performed on harpsichord,
organ, string quartet, brass ensemble, full orchestra,
and now -- on any S-100 system with a 4 MHz Z80 CPU
and a Cromemco D+7AIO analog interface card (real or
High-Nibble emulated), with the four voices summed
acoustically through two D+7AIO analog outputs.

FILES ON THIS DISK
------------------
  PLAYZ80.COM    The player program
  VOICES.MUS     Original 6-slot Cromemco wavetable bank
  CNT1.MUS       Contrapunctus 1   simple fugue
  CNT2.MUS       Contrapunctus 2   simple fugue (dotted)
  CNT3.MUS       Contrapunctus 3   simple, inverted subj.
  REG1.MUS       Contrapunctus 4   simple, inverted subj.
  REG2.MUS       Contrapunctus 9   double fugue at 12th
  DOU1.MUS       Contrapunctus 5   counter-fugue
  DOU2.MUS       Contrapunctus 6   counter-fugue, stylo francese
  INVER1.MUS     Contrapunctus 7   per aug. et dim.
  INVER2.MUS     Contrapunctus 10  double fugue at 10th
  MIR1.MUS       Contrapunctus 12  mirror fugue (rectus)
  TRI2.MUS       Contrapunctus 11  triple fugue
  UNFIN.MUS      Contrapunctus 14  the unfinished fugue
  AOF.SUB        SUBMIT batch -- plays all 12 in order
  AOF.QSB        QPM copy of AOF.SUB

To hear one movement:     A>PLAYZ80 CNT1.MUS
One pass with no prompts: A>PLAYZ80 CNT1.MUS /Q
Play all 12 in order:     A>SUBMIT AOF

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
and for the WTC Book I 4-voice fugue disk.

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
  D:/CPMEMU/disks/BachAOF-4v.unpacked/
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