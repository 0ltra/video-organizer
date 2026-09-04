import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

folder = Path(sys.argv[1]).expanduser()
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
        print(f"\nPossible duplicate group: '{base}'")
        # sort newest first
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        for i, f in enumerate(files):
            modified = datetime.fromtimestamp(f.stat().st_mtime)  # noqa: DTZ006
            tag = "  ← newest" if i == 0 else ""
            print(f"  {f.name} — modified {modified:%Y-%m-%d}{tag}")
