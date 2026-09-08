import argparse
import re
import shutil
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
    help="Show what would be moved, without moving anything",
)
parser.add_argument(
    "--apply",
    action="store_true",
    help="Actually move flagged files into a _review subfolder",
)
args = parser.parse_args()

folder = Path(args.folder).expanduser()
video_extensions = {".mp4", ".mov", ".avi", ".mkv"}
review_folder = folder / "_review"


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

any_flagged = False

for base, files in groups.items():
    if len(files) > 1:
        any_flagged = True
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        newest = files[0]
        older = files[1:]

        print(f"\nPossible duplicate group: '{base}'")
        modified = datetime.fromtimestamp(newest.stat().st_mtime)  # noqa: DTZ006
        print(f"  KEEP:   {newest.name} — modified {modified:%Y-%m-%d}")

        for f in older:
            modified = datetime.fromtimestamp(f.stat().st_mtime)  # noqa: DTZ006
            if args.apply:
                review_folder.mkdir(exist_ok=True)
                destination = review_folder / f.name
                shutil.move(str(f), str(destination))
                print(f"  MOVED:  {f.name} → _review/")
            elif args.dry_run:
                print(f"  WOULD MOVE: {f.name} — modified {modified:%Y-%m-%d}")
            else:
                print(f"  older:  {f.name} — modified {modified:%Y-%m-%d}")

if not any_flagged:
    print("No likely duplicates found.")
elif not args.dry_run and not args.apply:
    print(
        "\n(Run with --dry-run to preview, or --apply to move older versions into a _review folder)"
    )
