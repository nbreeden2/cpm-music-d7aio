"""Generate README.TXT for each Bach*.unpacked CP/M disk image.

Run once after this script is updated; outputs to
D:/CPMEMU/disks/<disk>.unpacked/0/README.TXT for each disk listed
in DISKS below.  The file is plain ASCII; CPMFMT.PY adds CRLF +
Ctrl-Z afterward.
"""
from pathlib import Path
from textwrap import dedent

DISK_ROOT = Path("D:/CPMEMU/disks")

# Per-disk metadata.  Each value is the body of the "THE MUSIC",
# "FILES ON THIS DISK", and "CONVERSION PROCESS" sections.  The
# rest of the file is identical boilerplate.
DISKS = {
    "BachCello1-G": dict(
        title="J.S. BACH -- SUITE No. 1 IN G MAJOR, BWV 1007  (SOLO CELLO)",
        music=dedent("""\
            On this disk you will find the seven movements of Bach's
            first unaccompanied Cello Suite (BWV 1007), composed around
            1717-1723 during his service at the court of Anhalt-Coethen.
            The Prelude is among the most familiar pieces in the
            classical repertoire; the remaining movements follow the
            standard Baroque suite plan of stylized dance forms --
            Allemande, Courante, Sarabande, two Minuets, and Gigue --
            drawn from across Europe.

            A solo cello has only four strings, so the music spends
            most of its time on one voice with brief double-stops at
            cadences and on heavier downbeats.  The player on this
            disk treats the source as a one-voice line with chord-
            moment detection: single notes ride on Voice 1 plus Voice
            3 (doubled with a custom cello timbre); on a two- or
            three-note chord, the doubling drops out and the extra
            notes take its place.
        """),
        files=dedent("""\
              PLAYZ80.COM    The player program
              VOICES.MUS     Wavetable bank (slot 2 = custom cello)
              PRELUDE.MUS    Movement 1 -- Prelude
              ALLEMAND.MUS   Movement 2 -- Allemande
              COURANTE.MUS   Movement 3 -- Courante
              SARABAND.MUS   Movement 4 -- Sarabande
              MINUET1.MUS    Movement 5 -- Minuet I
              MINUET2.MUS    Movement 6 -- Minuet II
              GIGUE.MUS      Movement 7 -- Gigue
              CELLO.SUB      SUBMIT batch -- plays all seven in order
              CELLO.QSB      QPM copy of CELLO.SUB

            To hear one movement:           A>PLAYZ80 PRELUDE.MUS
            One pass with no prompts:       A>PLAYZ80 PRELUDE.MUS /Q
            Play the whole suite in order:  A>SUBMIT CELLO
        """),
        conversion=dedent("""\
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
        """),
    ),

    "BachCello2-Eb": dict(
        title="J.S. BACH -- SUITE No. 4 IN Eb MAJOR, BWV 1010  (SOLO CELLO)",
        music=dedent("""\
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
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
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
        """),
    ),

    "BachInvent": dict(
        title="J.S. BACH -- TWO-PART INVENTIONS, BWV 772 - 786",
        music=dedent("""\
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
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
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
        """),
    ),

    "BachSinfonia": dict(
        title="J.S. BACH -- THREE-PART SINFONIAS, BWV 787 - 801",
        music=dedent("""\
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
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
            Mode '3' (sinfonia faithful) of midi2mus.py was used.
            Each of the three monophonic MIDI voice tracks is routed
            onto one physical voice: soprano on Voice 1 (sine), alto
            on Voice 2 (even-harmonic at the written pitch, sounding
            an octave higher per the wavetable shape), tenor / bass
            on Voice 3 (skewed saw at the written pitch).  Voice 4
            is silent, its timbre forced to sine so the wavetable
            DC offset on the second DAC channel is minimized.
        """),
    ),

    "BachSinfoniaAlt": dict(
        title="J.S. BACH -- THREE-PART SINFONIAS, BWV 787 - 801 (ALT)",
        music=dedent("""\
            On this disk you will find Bach's fifteen Three-Part
            Inventions ("Sinfonias", BWV 787 - 801), composed at
            Coethen around 1723, in an alternative four-voice
            arrangement.  The musical content is identical to the
            BachSinfonia disk; what differs is the timbre routing.
            Here the soprano line is fattened by a second voice
            playing the same notes through the octave-shifter
            wavetable, adding an octave-up "sparkle" reminiscent of
            the doubling on the original Cromemco BACH .MUS files.
            The alto and bass lines remain at their written pitch.
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
            Mode '2of3' (soprano octave-doubled sinfonia) of
            midi2mus.py was used.  Each of the three monophonic MIDI
            voice tracks is routed: soprano on Voice 1 (even-harmonic
            wavetable, sounding at the written pitch and giving the
            line body) AND Voice 3 (octave-shifter, adding an octave-
            up overtone); alto on Voice 2 (sine); bass on Voice 4
            (skewed saw at written pitch).  Compared with the
            BachSinfonia disk's "faithful" arrangement, this gives the
            top line more presence and brings out the imitative voice
            entries.
        """),
    ),

    "BachWTC1-4v": dict(
        title="J.S. BACH -- WELL-TEMPERED CLAVIER, BOOK I  (4-VOICE FUGUES)",
        music=dedent("""\
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
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
            Mode '4' (SATB chorale / 4-voice fugue) of midi2mus.py
            was used.  Each of the four monophonic MIDI voice tracks
            is routed one-to-one onto a physical voice at its written
            pitch -- soprano on Voice 1 (sine), alto on Voice 2
            (skewed saw), tenor on Voice 3 (square), bass on Voice 4
            (sine).  None of the voices uses an octave-shifting
            timbre, so what you hear matches the score.  This mode
            was added to the converter specifically for this disk
            and for the Art of Fugue disk.
        """),
    ),

    "BachWTC2": dict(
        title="J.S. BACH -- WELL-TEMPERED CLAVIER, BOOK II  (PRELUDES & FUGUES)",
        music=dedent("""\
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
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
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
        """),
    ),

    "BachAOF-4v": dict(
        title="J.S. BACH -- DIE KUNST DER FUGE, BWV 1080  (4-VOICE)",
        music=dedent("""\
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
        """),
        files=dedent("""\
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
        """),
        conversion=dedent("""\
            Mode '4' (SATB chorale / 4-voice fugue) of midi2mus.py
            was used.  Each of the four monophonic MIDI voice tracks
            is routed one-to-one onto a physical voice at its written
            pitch -- soprano on Voice 1 (sine), alto on Voice 2
            (skewed saw), tenor on Voice 3 (square), bass on Voice 4
            (sine).  None of the voices uses an octave-shifting
            timbre, so what you hear matches the score.  This mode
            was added to the converter specifically for this disk
            and for the WTC Book I 4-voice fugue disk.
        """),
    ),
}

# ---- shared boilerplate ---------------------------------------------------

PLAYER = dedent("""\
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
""")

MIXER = dedent("""\
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
""")

DISK_FORMAT_TEMPLATE = dedent("""\
    DISK FORMAT (.unpacked)
    -----------------------
    On the host PC, this disk is the folder
      D:/CPMEMU/disks/{disk}.unpacked/
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
""")

REPO = dedent("""\
    PROJECT REPOSITORY
    ------------------
    Source code for the player (PLAYZ80, PLAY8080, PLAYCDOS), the
    MIDI-to-MUS converter (midi2mus.py), the wavetable analysis
    scripts, and all of the disk images on this system:
      https://github.com/nbreeden2/cpm-music-d7aio
""")

MIDI_SRC = dedent("""\
    MIDI SOURCE
    -----------
    The score data was taken from Standard MIDI Files downloaded
    from the Bach Central MIDI archive:
      https://www.bachcentral.com/midiindexcomplete.html
""")

FOOTER = dedent("""\
    ------------------------------------------------------------------------
    Neil Breeden   <retrotechreboot@gmail.com>
""")


def render(name: str, meta: dict) -> str:
    bar = "=" * 72
    out = []
    out.append(bar)
    out.append(meta["title"])
    out.append(bar)
    out.append("")
    out.append("THE MUSIC")
    out.append("---------")
    out.append(meta["music"])
    out.append("FILES ON THIS DISK")
    out.append("------------------")
    out.append(meta["files"])
    out.append(MIDI_SRC)
    out.append("CONVERSION PROCESS")
    out.append("------------------")
    out.append(meta["conversion"])
    out.append(PLAYER)
    out.append(MIXER)
    out.append(DISK_FORMAT_TEMPLATE.format(disk=name))
    out.append(REPO)
    out.append(FOOTER)
    return "\n".join(out)


def main():
    # Emit CP/M-shaped text directly: CRLF line endings + trailing
    # 0x1A (Ctrl-Z) EOF marker.  This means CPMFMT.PY does not need
    # to be run after this generator -- the output is already valid
    # CP/M text.
    for name, meta in DISKS.items():
        dst = DISK_ROOT / f"{name}.unpacked" / "0" / "README.TXT"
        body = render(name, meta).replace("\r\n", "\n").replace("\n", "\r\n")
        dst.write_bytes(body.encode("ascii") + b"\x1a")
        print(f"wrote {dst}  ({dst.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
