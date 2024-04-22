from __future__ import annotations

import pytest

from extended_configparser.parser import ConfigMatcher

DELIMITER = ["=", ":"]
COMMENT_PREFIXES = ["#", ";"]


@pytest.mark.parametrize(
    "line,expected",
    [
        ("# This is a comment", True),
        ("; This is a = comment", True),
        ("  \t; This is a: comment", True),
        ("  \t# This is [a.comment]", True),
        ("This not", False),
        ("  \tThis.not", False),
        ("[This.not]", False),
        ("  \t[This.not]", False),
        ("this = not", False),
        ("this:not", False),
        ("", False),
        ("  \t", False),
    ],
)
def test_is_comment(line, expected):
    matcher = ConfigMatcher(delimiters=DELIMITER, comment_prefixes=COMMENT_PREFIXES)
    result = matcher.is_comment(line)
    assert result is expected


@pytest.mark.parametrize(
    ("line", "section"),
    (
        ("# This is a comment", None),
        ("; This is a = comment", None),
        ("  \t; This is a: comment", None),
        ("  \t# This is [a.comment]", None),
        ("This not", None),
        ("  \tThis.not", None),
        ("[This.not]", "This.not"),
        ("  \t[This.not]", "This.not"),
        ("this = not", None),
        ("this:not", None),
        ("", None),
        ("  \t", None),
    ),
)
def test_section(line, section):
    matcher = ConfigMatcher(delimiters=DELIMITER, comment_prefixes=COMMENT_PREFIXES)
    result = matcher.get_section(line)
    assert result == section


@pytest.mark.parametrize(
    ("line", "option"),
    (
        ("# This is a comment", None),
        ("; This is a = comment", None),
        ("  \t; This is a: comment", None),
        ("  \t# This is [a.comment]", None),
        ("This not", None),
        ("  \tThis.not", None),
        ("[This.not]", None),
        ("  \t[This.not]", None),
        ("this = is", "this"),
        ("  \tthis = is", "this"),
        ("this:not", "this"),
        ("  \tthis:not", "this"),
        ("", None),
        ("  \t", None),
    ),
)
def test_option(line, option):
    matcher = ConfigMatcher(delimiters=DELIMITER, comment_prefixes=COMMENT_PREFIXES)
    result = matcher.get_option(line)
    assert result == option
