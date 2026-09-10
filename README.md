video-organizer
------------------------------------------------------------
A command-line tool that scans a folder (recursively) for video files and flags likely clutter — duplicate exports and old versioned files — so you can clean up a messy project folder without hunting through it by hand.

Why
------------------------------------------------------------
Video editing exports pile up fast: project_v1.mp4, project_v2.mp4, project_final.mov, project_FINAL2.mov... it's easy to lose track of which file is actually the one you want, and duplicate/near-duplicate exports quietly eat up disk space.

This tool scans a folder and flags:
------------------------------------------------------------
Exact content duplicates — files that are byte-identical (or near-identical, based on size + sampled content), regardless of filename
Likely versioned exports — files that share a base name once common version markers (v1, v2, final, FINAL2, copy, etc.) are stripped out

In both cases, it keeps the newest file in each group and flags the rest.

How it works
-------------------------------------------------------------
Recursively scans the target folder for video files (.mp4, .mov, .avi, .mkv)
Groups files two ways: by content hash (sampling the start, middle, and end of each file for speed) and by filename after stripping version markers
Within each group, keeps the most recently modified file and flags the rest
Optionally moves flagged files into a _review/ subfolder — nothing is ever deleted, so you can review and clean up manually afterward
