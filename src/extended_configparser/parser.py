from __future__ import annotations
import configparser
import os

import logging
import re
from typing import Iterable
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

        self.comment_pattern = fr"^\s*([{r_comment_prefixes}])\s*(.+?)$"
        self.section_pattern = fr"^\s*\[([^\]]+)\]\s*$" 
        self.option_pattern = fr"^\s*(\b.+?\b)\s*?({r_delimiters})"

    def get_matches(self, text: str | Iterable[str]):
        """Yield comment matches found in the given text."""

        if type(text) is str:
            lines = text.split("\n")
        else:
            lines = text

        started = False
        current_section = None
        current_option = None
        current_comment_lines = []

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
    def clean_prefix(text: str, comment_prefixes: list[str], multiline=True):
        """Remove comment prefixes from a string."""

        if multiline:
            return "\n".join([line.lstrip(comment_prefixes + [" "]) for line in text.split("\n")])
        
        return text.lstrip(comment_prefixes)
        
    @staticmethod
    def add_prefix(text: str, prefix: str, multiline=True, add_space=True):
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
    def __init__(self, matcher: ConfigMatcher, raw_comment: str, section: str | None, option: str | None):
        self.matcher = matcher
        
        self.raw_comment = raw_comment
        """The raw comment string, including comment prefixes."""

        # Clean up the comment string
        lines = self.raw_comment.split("\n")
        for i, line in enumerate(lines):
            for prefix in matcher.comment_prefixes:
                if line.startswith(prefix):
                    lines[i] = line[len(prefix):].strip()
            
        self.comment: str = "\n".join(lines)
        """The comment string without comment prefixes."""

        self.section = section
        """The section the comment is in. None if the comment is the top comment and thus not in a section."""

        self.option = option
        """The option the comment is for. None if the comment is a section comment."""

        
        


class ExtendedConfigParser(configparser.ConfigParser):
    """ConfigParser that can write comments to a file."""
    
    def __init__(self, defaults=None, include_env_vars=False, dict_type=dict,
                 allow_no_value=False, *, delimiters=('=', ':'),
                 comment_prefixes=('#', ';'), inline_comment_prefixes=None,
                 strict=True, empty_lines_in_values=True,
                 default_section=configparser.DEFAULTSECT,
                 interpolation=configparser.ExtendedInterpolation(), converters=configparser._UNSET):
        if defaults is None:
            defaults = {}
        if include_env_vars:
            defaults.update(os.environ)
    


        super().__init__(
            defaults=defaults,
            dict_type=dict_type,
            allow_no_value=allow_no_value,
            delimiters=delimiters,
            comment_prefixes=comment_prefixes,
            inline_comment_prefixes=inline_comment_prefixes,
            strict=strict,
            empty_lines_in_values=empty_lines_in_values,
            default_section=default_section,
            interpolation=interpolation,
            converters=converters
        )
        
        self.top_comment = None
        self.end_comment = None
        self._option_comments: dict[str, dict[str, str]] = {}
        self._section_comments: dict[str, str] = {}
        self._delimiters = delimiters
        self._comment_prefixes = comment_prefixes

    def parse_comments(self, text: str | Iterable[str]) -> None:

        matcher = ConfigMatcher(self._delimiters, self._comment_prefixes)
        matches = list(matcher.get_matches(text))
        # print("Matches:", len(matches))
        for m in matches:
            # print("Match:", m.comment, m.section, m.option)
            if m.section is None and m.option is None:
                if self.top_comment is None:
                    self.top_comment = m.comment
                else:
                    self.end_comment = m.comment
            else:
                self.set_comment(m.section, m.option, m.comment)

    def read(self, filenames, encoding=None):
        """Read and parse a filename or an iterable of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify an iterable of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the iterable will be read.  A single
        filename may also be given.

        Return list of successfully read files.
        """
        if isinstance(filenames, (str, os.PathLike)):
            filenames = [filenames]
        for filename in filenames:
            with open(filename, encoding=encoding) as f:
                self.read_file(f, filename)
                self.parse_comments(f.read())

    def read_file(self, f, source):
        """Like read() but the argument must be a file-like object.

        The `f` argument must be iterable, returning one line at a time.
        Optional second argument is the `source` specifying the name of the
        file being read. If not given, it is taken from f.name. If `f` has no
        `name` attribute, `<???>` is used.
        """
        super().read_file(f, source)
        f.seek(0)
        self.parse_comments(f)
    
    def get_comment(self, section: str, option: str = None) -> str:

        if option is None:
            return self._section_comments.get(section, "")
        
        option = option.lower()
        return self._option_comments.get(section, {}).get(option, "")

    def set_comment(self, section: str, option: str, comment: str):
        if not section and not option:
            return
        
        if not section:
            return
        
        if not option:
            if section not in self._section_comments:
                self._section_comments[section] = comment
            return
        
        option = option.lower()
        if section not in self._option_comments:
            self._option_comments[section] = {}
        
        self._option_comments[section][option] = comment

    def set(self, section: str, option: str, value: str | None, comment: str | None = None):
        super().set(section, option, value)
        if comment:
            self.set_comment(section, option, comment)

    def write(self, fp, space_around_delimiters=True):
        """Write an .ini-format representation of the configuration state.

        If `space_around_delimiters` is True (the default), delimiters
        between keys and values are surrounded by spaces.

        Please note that comments in the original configuration file are not
        preserved when writing the configuration back.
        """
        if space_around_delimiters:
            d = " {} ".format(self._delimiters[0])
        else:
            d = self._delimiters[0]

        if self.top_comment:
            fp.write(ConfigMatcher.add_prefix(self.top_comment, self._comment_prefixes[0]) + "\n\n")

        if self._defaults:
            self._write_section(fp, self.default_section,
                                    self._defaults.items(), d)
        for section in self._sections:
            self._write_section(fp, section,
                                self._sections[section].items(), d)
            
        if self.end_comment:
            fp.write(ConfigMatcher.add_prefix(self.end_comment, self._comment_prefixes[0]))

    def _write_section(self, fp, section_name: str, section_items: dict[str, str], delimiter: str):
        """Write a single section to the specified `fp`."""
        if section_name in self._section_comments:
            comment = self._section_comments[section_name]
            fp.write(ConfigMatcher.add_prefix(comment, self._comment_prefixes[0]) + "\n")
                
        fp.write("[{}]\n".format(section_name))
        for key, value in section_items:
            value = self._interpolation.before_write(self, section_name, key,
                                                     value)
            if value is not None or not self._allow_no_value:
                value = delimiter + str(value).replace('\n', '\n\t')
            else:
                value = ""

            comment = self._option_comments.get(section_name, {}).get(key, "")
            if comment:
                fp.write("{}\n".format(ConfigMatcher.add_prefix(comment, self._comment_prefixes[0])))
            fp.write("{}{}\n".format(key, value))
        fp.write("\n")