"""Tests for csv delimiter detector."""

from scripts.detect_delimiter import detect_delimiter


def test_detect_comma() -> None:
    assert detect_delimiter("a,b,c\n1,2,3\n4,5,6") == ","


def test_detect_tab() -> None:
    assert detect_delimiter("a\tb\tc\n1\t2\t3\n") == "\t"


def test_detect_semicolon() -> None:
    assert detect_delimiter("name;age;city\nalice;30;nyc\nbob;25;lon") == ";"
