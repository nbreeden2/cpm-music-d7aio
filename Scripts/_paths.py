"""Shared path constants for the MUSIC project's Scripts/ tooling.

The 2026-05-11 reorganization split the project into:
    Original_CPM_Files/   - CDOS-shipped disk image, preserved as-is
    New_CPM_Files/        - modern CP/M disk: regenerated .MUS + player builds
    Scripts/              - this directory; all .py tooling
    Voice_Tests/          - timbre test .MUS + simulator .wav output
    voices_analysis/      - generated analysis artifacts

All scripts that read or write on-disk files should import from here.
Future reorgs only need to update this single file.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ORIGINAL_DISK   = PROJECT_ROOT / "Original_CPM_Files"
NEW_DISK        = PROJECT_ROOT / "New_CPM_Files"
VOICE_TESTS     = PROJECT_ROOT / "Voice_Tests"
VOICES_ANALYSIS = PROJECT_ROOT / "voices_analysis"

# Canonical source-of-truth artifacts (untouched since reorg):
VOICES_MUS = ORIGINAL_DISK / "VOICES.MUS"
PLAY_COM   = ORIGINAL_DISK / "PLAY.COM"
