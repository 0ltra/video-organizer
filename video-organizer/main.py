import argparse
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(
    description="Scan a folder for video files and flag likely duplicate/versioned exports."
)
parser.add_argument("folder", help="Folder to scan")
parser.add_argument(
    "--dry-run",
    action="store_true",
    help="Show what would be deleted, without deleting anything",
)
args = parser.parse_args()

folder = Path(args.folder).expanduser()
video_extensions = {".mp4", ".mov", ".avi", ".mkv"}


def get_base_name(name):
    name = re.sub(
        r"(_|\s)?(v\d+|final\d*|FINAL\d*|copy)", "", name, flags=re.IGNORECASE
    )
    return name.strip().lower()


groups = defaultdict(list)

for file in folder.rglob("*"):
    if file.is_file() and file.suffix.lower() in video_extensions:
        base = get_base_name(file.stem)
        groups[base].append(file)

for base, files in groups.items():
    if len(files) > 1:
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        newest = files[0]
        older = files[1:]

        print(f"\nPossible duplicate group: '{base}'")
        modified = datetime.fromtimestamp(newest.stat().st_mtime)  # noqa: DTZ006
        print(f"  KEEP:   {newest.name} — modified {modified:%Y-%m-%d}")

        for f in older:
            modified = datetime.fromtimestamp(f.stat().st_mtime)  # noqa: DTZ006
            if args.dry_run:
                print(f"  WOULD DELETE: {f.name} — modified {modified:%Y-%m-%d}")
            else:
                print(f"  older:  {f.name} — modified {modified:%Y-%m-%d}")

if not args.dry_run:
    print("\n(Run with --dry-run to preview what would be deleted)")
