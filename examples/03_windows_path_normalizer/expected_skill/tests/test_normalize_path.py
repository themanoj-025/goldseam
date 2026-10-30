"""Tests for windows path normalizer."""

from scripts.normalize_path import normalize_windows_path


def test_normalize_backslashes() -> None:
    assert normalize_windows_path("C:\\Users\\user\\data.txt") == "C:/Users/user/data.txt"


def test_sanitize_reserved_device() -> None:
    assert normalize_windows_path("dir\\NUL.txt") == "dir/safe_NUL.txt"
    assert normalize_windows_path("COM1") == "safe_COM1"
