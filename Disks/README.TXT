========================================================================
DISK IMAGES FOR THE D+7AIO MUSIC PLAYER
========================================================================

This folder is the committed archive of every CP/M disk image used
with the PLAYZ80 / PLAY8080 / PLAY (CDOS) music player programs.
Each disk is present in TWO forms:

  *.dsk        Packed image (256 256-byte sectors -- the standard
               CP/M-flavored floppy image used by fdcServer and
               Z80Pack).  Suitable for writing to a uSD card for a
               real IMSAI 8080 with an SDH-100, for booting an
               emulator that wants a packed image, or for archive.

  *.unpacked/  Host-side folder tree of the same content.  fdcServer
               serves the same files directly from this layout
               without having to repack; numbered subfolders 0/..15/
               are the CP/M USER areas.  Edit a file inside one of
               these folders on the host and CP/M sees the change
               on the next BDOS read.  fdcServer creates and manages
               two hidden files at the disk root ($BOOT and $ATTR);
               do not edit those by hand.

For a deeper description of either format, see the High Nibble
fdcServer documentation:
  https://thehighnibble.com/sdh100/fdc-server/#table-of-contents

------------------------------------------------------------------------
DISKS IN THIS ARCHIVE
------------------------------------------------------------------------

Each disk carries PLAYZ80.COM, a VOICES.MUS wavetable bank, the
.MUS files for the music itself, an .SUB / .QSB SUBMIT batch that
plays every piece in order under PLAYZ80's /Q (quiet) switch, and
a README.TXT describing the music and the conversion process used.

  BachAOF-4v       Bach -- Die Kunst der Fuge, BWV 1080
                   12 four-voice movements (contrapuncti, regular
                   fugues, counter-fugues, inversions, mirror,
                   triple, the unfinished quadruple fugue)

  BachCello1-G     Bach -- Cello Suite No. 1 in G major, BWV 1007
                   7 movements (Prelude / Allemande / Courante /
                   Sarabande / Minuet I / Minuet II / Gigue)

  BachCello2-Eb    Bach -- Cello Suite No. 4 in Eb major, BWV 1010
                   6 movements (Prelude / Allemande / Courante /
                   Sarabande / Bourree / Gigue)
                   (Disk name "2" reflects "second cello disk
                   made", not "Cello Suite No. 2"; this is Suite 4.)

  BachInvent       Bach -- Two-Part Inventions, BWV 772 - 786
                   15 inventions, in BWV order

  BachSinfonia     Bach -- Three-Part Inventions (Sinfonias),
                   BWV 787 - 801; faithful three-voice arrangement

  BachSinfoniaAlt  Same 15 sinfonias as BachSinfonia, but with the
                   soprano line octave-doubled

  BachWTC1-4v      Bach -- Well-Tempered Clavier, Book I
                   8 four-voice fugues from BWV 846 - 869

  BachWTC2         Bach -- Well-Tempered Clavier, Book II
                   21 of the 48 prelude/fugue movements,
                   BWV 870 - 881 (the rest were corrupt in the
                   source MIDI corpus)

  music            The "system" disk -- preserved copy of the
                   original Cromemco CDOS music floppy: PLAY.COM,
                   VOICES.MUS, and the eighteen CDOS-era .MUS
                   songs (BACH1 - BACH15, ENT, GOLDEN, JILLA,
                   LOVEBLUE, MICHAEL, ML, NEWWORLD, POMP, TEST).

  TETRIS-Music     Korobeiniki (the Tetris main theme) plus GB
                   and NES remixes; CUSTOM VOICES.MUS with the
                   "triangle" wavetable in slot 2.

For per-disk track lists, conversion details, and credits, see the
README.TXT inside each disk's USER 0 folder
(e.g. Disks/BachAOF-4v.unpacked/0/README.TXT).

------------------------------------------------------------------------
THE PLAYER PROGRAM
------------------------------------------------------------------------

PLAYZ80 is a 4-voice wavetable synthesizer for the Cromemco D+7AIO
analog interface card.  It runs on any S-100 system with a 4 MHz
Z80 CPU and a D+7AIO (real, or High-Nibble emulated).  Source for
PLAYZ80, PLAY8080, PLAYCDOS (a bit-perfect reassembly of the
original PLAY.COM), the MIDI-to-MUS converter, and the per-disk
build steps lives in the project repository:

  https://github.com/nbreeden2/cpm-music-d7aio

------------------------------------------------------------------------
Neil Breeden   <retrotechreboot@gmail.com>
