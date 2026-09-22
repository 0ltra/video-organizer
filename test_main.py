from main import (
    get_base_name,
    group_by_content,
    group_by_name,
    quick_hash,
    scan_video_files,
)

# get_base_name


def test_strips_version_number():
    assert get_base_name("project_v1") == "project"
    assert get_base_name("project_v12") == "project"


def test_strips_final_variants():
    assert get_base_name("project_final") == "project"
    assert get_base_name("project_FINAL2") == "project"


def test_leaves_unrelated_names_alone():
    assert get_base_name("random_clip") == "random_clip"


# scan_video_files


def test_finds_only_video_extensions(tmp_path):
    (tmp_path / "clip.mp4").touch()
    (tmp_path / "notes.txt").touch()
    (tmp_path / "movie.mov").touch()

    found = scan_video_files(tmp_path)
    names = {f.name for f in found}

    assert names == {"clip.mp4", "movie.mov"}


def test_finds_files_in_subfolders(tmp_path):
    subfolder = tmp_path / "nested"
    subfolder.mkdir()
    (subfolder / "deep_clip.mp4").touch()

    found = scan_video_files(tmp_path)
    names = {f.name for f in found}

    assert "deep_clip.mp4" in names


# quick_hash


def test_identical_content_same_hash(tmp_path):
    file_a = tmp_path / "a.mp4"
    file_b = tmp_path / "b.mp4"
    file_a.write_bytes(b"same content")
    file_b.write_bytes(b"same content")

    assert quick_hash(file_a) == quick_hash(file_b)


def test_different_content_different_hash(tmp_path):
    file_a = tmp_path / "a.mp4"
    file_b = tmp_path / "b.mp4"
    file_a.write_bytes(b"content one")
    file_b.write_bytes(b"totally different content")

    assert quick_hash(file_a) != quick_hash(file_b)


# group_by_content


def test_groups_identical_files(tmp_path):
    file_a = tmp_path / "clip_a.mp4"
    file_b = tmp_path / "clip_b.mp4"
    file_a.write_bytes(b"duplicate data")
    file_b.write_bytes(b"duplicate data")

    files = scan_video_files(tmp_path)
    groups = group_by_content(files)

    assert len(groups) == 1
    group = next(iter(groups.values()))
    assert len(group) == 2


def test_no_group_for_unique_files(tmp_path):
    (tmp_path / "a.mp4").write_bytes(b"one")
    (tmp_path / "b.mp4").write_bytes(b"two")

    files = scan_video_files(tmp_path)
    groups = group_by_content(files)

    assert groups == {}


# group_by_name


def test_groups_versioned_filenames(tmp_path):
    (tmp_path / "project_v1.mp4").touch()
    (tmp_path / "project_v2.mp4").touch()
    (tmp_path / "unrelated.mp4").touch()

    files = scan_video_files(tmp_path)
    groups = group_by_name(files)

    assert "project" in groups
    assert len(groups["project"]) == 2
    assert "unrelated" not in groups
