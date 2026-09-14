video-organizer

A CLI tool that scans a folder full of video exports and flags the clutter — duplicate files and old versions — so you're not manually hunting through project_v1.mp4, project_v2.mp4, and project_FINAL2.mov trying to remember which one actually matters.

What it does

This started as a simple recursive file scanner and grew into a two-strategy duplicate detector:

Content-based duplicate detection – hashes each file (sampling the start, middle, and end for speed) to catch files that are byte-identical regardless of filename
Filename-based version detection – strips common version markers (v1, v2, final, FINAL2, copy, etc.) to group files that are clearly different versions of the same export
--dry-run – preview exactly what would be flagged and moved, without touching anything
--apply – actually move flagged files into a _review/ subfolder — nothing is ever deleted, so any mistake is fully reversible
Tech stack
Python 3, standard library only (pathlib, argparse, hashlib, re, shutil, collections)
pytest for testing the core scanning/hashing/grouping logic
Git + GitHub for version control
Function-based architecture — scanning, hashing, grouping, reporting, and moving are all separated into single-purpose functions
Running it locally

You'll need Python 3.9+.

bash
git clone https://github.com/yourusername/video-organizer.git
cd video-organizer
python3 -m venv venv
source venv/bin/activate
python3 -m pip install pytest   # only needed to run the test suite

Then run it against any folder:

bash
python3 main.py /path/to/folder --dry-run
python3 main.py /path/to/folder --apply
Running tests
bash
python3 -m pytest

Covers filename parsing (get_base_name), recursive file scanning, content hashing, and both grouping strategies — using pytest's tmp_path fixture so every test runs against a fresh temporary folder instead of real files on disk.

Project structure
video-organizer/
├── main.py           # CLI entry point + all scanning/grouping/moving logic
├── test_main.py       # pytest suite
└── venv/               # local virtual environment (not committed)
Notes
Duplicate detection samples ~1MB from the start, middle, and end of each file rather than hashing the whole thing — full-file hashing on multi-GB video exports would be slow, and sampling reliably catches true duplicates without reading gigabytes of data per run.
A file can be flagged by either detection strategy (or both) but only gets moved once — flagged files are deduplicated before the move step runs.
Possible next steps: a config file for custom extensions/version patterns, and a C++/pybind11 component for the hashing step as a performance exercise.
