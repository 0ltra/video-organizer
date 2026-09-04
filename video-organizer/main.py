import sys
from datetime import datetime
from pathlib import Path

folder = Path(sys.argv[1]).expanduser()

video_extensions = {".mp4", ".mov", ".avi", ".mkv"}

for file in folder.rglob("*"):
    if file.is_file() and file.suffix.lower() in video_extensions:
        size_mb = file.stat().st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(file.stat().st_mtime)  # noqa: DTZ006
        print(f"{file.name} — {size_mb:.1f} MB — modified {modified:%Y-%m-%d}")
