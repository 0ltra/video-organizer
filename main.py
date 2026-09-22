import argparse
import hashlib
import re
import shutil
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Config
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}
SAMPLE_SIZE = 1024 * 1024  # 1 MB sampled from start/middle/end for hashing
VERSION_PATTERN = re.compile(r"(_|\s)?(v\d+|final\d*|FINAL\d*|copy)", re.IGNORECASE)
REVIEW_FOLDER_NAME = "_review"
MAX_WORKERS = 8  # number of files to hash concurrently


def get_base_name(name):
    """Strip common version markers to find a file's 'base' name for grouping."""
    return VERSION_PATTERN.sub("", name).strip().lower()


def quick_hash(file_path):
    """Hash based on file size + samples from start/middle/end. Fast, catches true duplicates without reading whole files."""
    size = file_path.stat().st_size
    hasher = hashlib.blake2b()
    hasher.update(str(size).encode())

    try:
        with open(file_path, "rb") as f:
            hasher.update(f.read(SAMPLE_SIZE))
            if size > SAMPLE_SIZE * 3:
                f.seek(size // 2)
                hasher.update(f.read(SAMPLE_SIZE))
                f.seek(max(size - SAMPLE_SIZE, 0))
                hasher.update(f.read(SAMPLE_SIZE))
    except (OSError, PermissionError) as e:
        print(
            f"  Warning: couldn't read {file_path.name} ({e}), skipping",
            file=sys.stderr,
        )
        return None

    return hasher.hexdigest()


def scan_video_files(folder):
    """Recursively find all video files in a folder."""
    return [
        f
        for f in folder.rglob("*")
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS
    ]


def group_by_content(video_files, parallel=True):
    """Group files that are byte-identical (or near-identical via sampling).
    Hashing is I/O-bound (mostly waiting on disk reads), so a thread pool lets
    multiple files be read/hashed concurrently instead of one at a time.
    """
    groups = defaultdict(list)

    if parallel and len(video_files) > 1:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            hashes = list(executor.map(quick_hash, video_files))
    else:
        hashes = [quick_hash(f) for f in video_files]

    for f, h in zip(video_files, hashes):
        if h is not None:
            groups[h].append(f)

    return {h: files for h, files in groups.items() if len(files) > 1}


def group_by_name(video_files):
    """Group files that share a base name after stripping version markers."""
    groups = defaultdict(list)
    for f in video_files:
        base = get_base_name(f.stem)
        groups[base].append(f)
    return {base: files for base, files in groups.items() if len(files) > 1}


def sort_newest_first(files):
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def report_groups(groups, label):
    flagged = []
    print(f"\n=== {label} ===")
    if not groups:
        print("None found.")
        return flagged

    for key, files in groups.items():
        files = sort_newest_first(files)
        newest, older = files[0], files[1:]
        print(f"\nGroup: '{key}'" if isinstance(key, str) else "\nGroup:")
        print(f"  KEEP: {newest.name}")
        for f in older:
            print(f"  flagged: {f.name}")
            flagged.append(f)
    return flagged


def apply_moves(files, folder, dry_run, apply):
    if not files:
        return
    review_folder = folder / REVIEW_FOLDER_NAME

    if apply:
        review_folder.mkdir(exist_ok=True)
        for f in files:
            try:
                shutil.move(str(f), str(review_folder / f.name))
                print(f"  MOVED: {f.name} → {REVIEW_FOLDER_NAME}/")
            except (OSError, PermissionError) as e:
                print(f"  ERROR moving {f.name}: {e}", file=sys.stderr)
    elif dry_run:
        for f in files:
            print(f"  WOULD MOVE: {f.name}")
    else:
        print(
            f"\n(Run with --dry-run to preview, or --apply to move flagged files into {REVIEW_FOLDER_NAME}/)"
        )


def run_benchmark(video_files):
    """Compare sequential vs. parallel hashing time on the current file set."""
    print(f"\n=== Benchmark: hashing {len(video_files)} file(s) ===")

    start = time.perf_counter()
    group_by_content(video_files, parallel=False)
    sequential_time = time.perf_counter() - start

    start = time.perf_counter()
    group_by_content(video_files, parallel=True)
    parallel_time = time.perf_counter() - start

    print(f"Sequential: {sequential_time:.3f}s")
    print(f"Parallel:   {parallel_time:.3f}s")
    if parallel_time > 0:
        print(f"Speedup:    {sequential_time / parallel_time:.2f}x")


def main():
    parser = argparse.ArgumentParser(
        description="Scan a folder for video files and flag likely duplicate/versioned exports."
    )
    parser.add_argument("folder", help="Folder to scan")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be moved"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually move flagged files into a review folder",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Compare sequential vs. parallel hashing speed",
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser()

    if not folder.exists():
        print(f"Error: folder does not exist: {folder}", file=sys.stderr)
        sys.exit(1)
    if not folder.is_dir():
        print(f"Error: not a folder: {folder}", file=sys.stderr)
        sys.exit(1)

    try:
        video_files = scan_video_files(folder)
    except PermissionError as e:
        print(f"Error: permission denied reading {folder} ({e})", file=sys.stderr)
        sys.exit(1)

    if args.benchmark:
        run_benchmark(video_files)
        return

    content_groups = group_by_content(video_files)
    name_groups = group_by_name(video_files)

    content_flagged = report_groups(content_groups, "Exact content duplicates")
    name_flagged = report_groups(name_groups, "Likely versioned exports (by filename)")

    all_flagged = list(dict.fromkeys(content_flagged + name_flagged))

    if all_flagged:
        print(f"\n{len(all_flagged)} file(s) flagged.")
        apply_moves(all_flagged, folder, args.dry_run, args.apply)


if __name__ == "__main__":
    main()
