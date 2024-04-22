from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from collections.abc import Iterator

logger = logging.getLogger(__name__)


class ConfigMatcher:
    """
    A class that can match comments, sections and options in a configuration file.
    The matcher depends on the delimiter and comment prefixe definition used in the configuration file.
    """

    def __init__(self, delimiters: list[str], comment_prefixes: list[str]):
        """Initialize the config matcher.

        Parameters
        ----------
        delimiters : list[str]
            Delimiters used in the configuration file to separate options from values.
        comment_prefixes : list[str]
            Symbols used to indicate a comment in the configuration file.
        """
        self.delimiters = delimiters
        self.comment_prefixes = comment_prefixes

        r_delimiters = "|".join(re.escape(d) for d in self.delimiters)
        r_comment_prefixes = "".join(re.escape(p) for p in self.comment_prefixes)

        self.comment_pattern = rf"^\s*([{r_comment_prefixes}])\s*(.+?)$"
        self.section_pattern = rf"^\s*\[([^\]]+)\]\s*$"
        self.option_pattern = rf"^\s*(\b.+?\b)\s*?({r_delimiters})"

    def get_matches(self, text: str | Iterable[str]) -> Iterator[CommentMatch]:
        """Yield comment matches found in the given text."""

        lines: list[str] | Iterable[str]

        if type(text) is str:
            lines = text.split("\n")
        else:
            lines = text

        started = False
        current_section = None
        current_option = None
        current_comment_lines: list[str] = []

        for line in lines:
            if self.is_empty(line):
                if len(current_comment_lines) > 0 and not started:
                    started = True
                    yield CommentMatch(self, "\n".join(current_comment_lines), current_section, current_option)

                current_comment_lines = []
                continue

            # Check this first, because comments can contain delimiters or other stuff
            if self.is_comment(line):
                current_comment_lines.append(line.strip())
                continue

            started = True
            if (section := self.get_section(line)) is not None:
                current_section = section
                current_option = None

                if len(current_comment_lines) > 0:
                    yield CommentMatch(self, "\n".join(current_comment_lines), current_section, None)

                current_comment_lines = []
                continue

            if (option := self.get_option(line)) is not None:
                current_option = option

                if len(current_comment_lines) > 0:
                    yield CommentMatch(self, "\n".join(current_comment_lines), current_section, current_option)

                current_comment_lines = []
                continue

        if len(current_comment_lines) > 0:
            yield CommentMatch(self, "\n".join(current_comment_lines), None, None)

    @staticmethod
    def clean_prefix(text: str, comment_prefixes: list[str], multiline: bool = True) -> str:
        """Remove comment prefixes from a string."""

        if multiline:
            return "\n".join([line.lstrip("".join(comment_prefixes + [" "])) for line in text.split("\n")])

        return text.lstrip("".join(comment_prefixes))

    @staticmethod
    def add_prefix(text: str, prefix: str, multiline: bool = True, add_space: bool = True) -> str:
        """Add a comment prefix to a string."""

        if add_space:
            prefix = prefix.strip() + " "

        if multiline:
            # Add prefix only if the line does not start with a comment prefix
            return "\n".join([prefix + line if not line.startswith(prefix) else line for line in text.split("\n")])

        return prefix + text if not text.startswith(prefix) else text

    @staticmethod
    def is_empty(line: str) -> bool:
        return len(line.strip()) == 0

    def is_comment(self, line: str) -> bool:
        """Return True if the line is a comment."""
        return bool(re.match(self.comment_pattern, line))

    def get_section(self, line: str) -> str | None:
        """Return the section name if the line is a section line, otherwise None."""
        match = re.match(self.section_pattern, line)
        if match:
            return match.group(1).strip()
        return None

    def get_option(self, line: str) -> str | None:
        """Return the option name if the line is an option line, otherwise None."""
        match = re.match(self.option_pattern, line)
        if match:
            return match.group(1).strip()
        return None


class CommentMatch:
    def __init__(self, matcher: ConfigMatcher, raw_comment: str, section: str | None, option: str | None) -> None:
        self.matcher = matcher

        self.raw_comment = raw_comment
        """The raw comment string, including comment prefixes."""

        # Clean up the comment string
        lines = self.raw_comment.split("\n")
        for i, line in enumerate(lines):
            for prefix in matcher.comment_prefixes:
                if line.startswith(prefix):
                    lines[i] = line[len(prefix) :].strip()

        self.comment: str = "\n".join(lines)
        """The comment string without comment prefixes."""

        self.section = section
        """The section the comment is in. None if the comment is the top comment and thus not in a section."""

        self.option = option
        """The option the comment is for. None if the comment is a section comment."""
