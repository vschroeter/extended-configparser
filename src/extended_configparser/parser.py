from __future__ import annotations

import configparser
import logging
import os
from typing import Any
from typing import Iterable

logger = logging.getLogger(__name__)

from extended_configparser.matcher import ConfigMatcher


class ExtendedConfigParser(configparser.ConfigParser):
    """
    ConfigParser that can read from and write comments to a file.

    Use get_comment(section, option) and set_comment(section, option, comment) to get and set comments
    or use it directly when setting values with set(section, option, value, comment).
    """

    def __init__(
        self,
        defaults=None,
        dict_type=dict,
        allow_no_value: bool = False,
        *,
        delimiters=("=", ":"),
        comment_prefixes=("#", ";"),
        inline_comment_prefixes=None,
        strict: bool = True,
        empty_lines_in_values: bool = True,
        default_section=configparser.DEFAULTSECT,
        interpolation: configparser.Interpolation = configparser.ExtendedInterpolation(),
        ignore_non_existent_files: bool = True,
        converters=configparser._UNSET,
    ) -> None:
        if defaults is None:
            defaults = {}

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
            converters=converters,
        )

        self.top_comment = None
        self.end_comment = None
        self._option_comments: dict[str, dict[str, str | None]] = {}
        self._section_comments: dict[str, str | None] = {}
        self._delimiters = delimiters
        self._comment_prefixes = comment_prefixes
        self._ignore_non_existent_files = ignore_non_existent_files

    #############################################################################
    ### INTERNAL AND OVERRIDE METHODS
    #############################################################################

    def read(self, filenames, encoding=None) -> list[str]:
        """Read and parse a filename or an iterable of filenames.

        Files that cannot be opened are silently ignored; this is
        designed so that you can specify an iterable of potential
        configuration file locations (e.g. current directory, user's
        home directory, systemwide directory), and all existing
        configuration files in the iterable will be read.  A single
        filename may also be given.

        Return list of successfully read files.
        """
        paths_ok = []
        if isinstance(filenames, (str, os.PathLike)):
            filenames = [filenames]
        for filename in filenames:
            if os.path.exists(filename) and os.path.isfile(filename):
                try:
                    with open(filename, encoding=encoding) as f:
                        self.read_file(f, filename)
                        self._parse_comments(f.read())
                except OSError:
                    continue
                paths_ok.append(filename)
            elif not self._ignore_non_existent_files:
                logger.warning(f"File {filename} does not exist.")

        return paths_ok

    def read_file(self, f, source=None) -> None:
        """Like read() but the argument must be a file-like object.

        The `f` argument must be iterable, returning one line at a time.
        Optional second argument is the `source` specifying the name of the
        file being read. If not given, it is taken from f.name. If `f` has no
        `name` attribute, `<???>` is used.
        """
        super().read_file(f, source)
        f.seek(0)
        self._parse_comments(f)

    def write(self, fp, space_around_delimiters=True) -> None:
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
            self._write_section(fp, self.default_section, self._defaults.items(), d)
        for section in self._sections:
            self._write_section(fp, section, self._sections[section].items(), d)

        if self.end_comment:
            fp.write(ConfigMatcher.add_prefix(self.end_comment, self._comment_prefixes[0]))

    def _write_section(self, fp, section_name: str, section_items: dict[str, str], delimiter: str) -> None:
        """Write a single section to the specified `fp`."""
        if section_name in self._section_comments:
            comment = self._section_comments[section_name]
            if comment is not None:
                fp.write(ConfigMatcher.add_prefix(comment, self._comment_prefixes[0]) + "\n")

        fp.write("[{}]\n".format(section_name))
        for key, value in section_items:
            value = self._interpolation.before_write(self, section_name, key, value)
            if value is not None or not self._allow_no_value:
                value = delimiter + str(value).replace("\n", "\n\t")
            else:
                value = ""

            comment = self._option_comments.get(section_name, {}).get(key, "")
            if comment:
                fp.write("{}\n".format(ConfigMatcher.add_prefix(comment, self._comment_prefixes[0])))
            fp.write("{}{}\n".format(key, value))
        fp.write("\n")

    def _parse_comments(self, text: str | Iterable[str]) -> None:
        """Internal function to parse comments from the content string of a file."""

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

    def __str__(self) -> str:
        from io import StringIO

        s = StringIO()
        self.write(s)
        return s.getvalue()

    #############################################################################
    ### PUBLIC METHODS
    #############################################################################

    def get_comment(self, section: str, option: str | None = None) -> str | None:
        """Return the comment for a section or option.

        Parameters
        ----------
        section : str
            Section name
        option : str, optional
            Option name. If None, the comment for the section is returned.
        Returns
        -------
        str | None
            The comment for the section or option.
        """
        if option is None:
            return self._section_comments.get(section, None)

        option = option.lower()
        return self._option_comments.get(section, {}).get(option, "")

    def set_comment(self, section: str | None, option: str | None = None, comment: str | None = None) -> None:
        """Set a comment for a section or option.

        Parameters
        ----------
        section : str
            Section name
        option : str, optional
            Option name. If None, the comment is set for the section, by default None
        comment : str, optional
            Comment to set
        """
        if section is None and option is None:
            return

        if section is None:
            return

        if option is None:
            self._section_comments[section] = comment
            return

        option = option.lower()
        if section not in self._option_comments:
            self._option_comments[section] = {}

        self._option_comments[section][option] = comment

    def set(
        self, section: str, option: str, value: str | None, comment: str | None = None, add_section_if_missing=True
    ):
        """Set an option in a section.
        Optionally set a comment for the option.
        """
        if not self.has_section(section) and add_section_if_missing:
            self.add_section(section)

        if option is None:
            logger.error("Option name cannot be None @ setting %s to %s", section, value)
            return

        super().set(section, option, value)
        if comment:
            self.set_comment(section, option, comment)

    def add_section(self, section: str, comment: str | None = None):
        """Add a section to the configuration.
        Optionally set a comment for the section.
        """
        super().add_section(section)
        if comment:
            self.set_comment(section, comment=comment)

    #############################################################################
    ### ADDITIONAL GETTER METHODS
    #############################################################################

    @staticmethod
    def split_to_list(list_str: str, delimiter: str = ",", remove_brackets=["[]"]) -> list[str]:
        if list_str is None or list_str == "":
            return []

        for bracket in remove_brackets:
            list_str = list_str.lstrip(bracket).rstrip(bracket)

        return [i.strip() for i in list_str.split(delimiter) if len(i.strip()) > 0]

    @staticmethod
    def list_to_str(list: list[str] | str, delimiter: str = ",", brackets: str = "[]") -> str:
        if isinstance(list, str):
            return list
        s = delimiter.join(list)
        if brackets and len(brackets) == 2:
            s = brackets[0] + s + brackets[1]
        return s

    def get_list(self, section: str, option: str, delimiter: str = ",", fallback: Any = None) -> list[str]:
        """Get a list from a configuration option.

        Parameters
        ----------
        section : str
            Section name
        option : str
            Option name
        delimiter : str, optional
            List delimiter, by default ","
        fallback : _type_, optional
            Fallback value, by default None

        Returns
        -------
        list[str]
            The list
        """
        v = self.get(section, option, fallback=None)
        if v is None:
            return fallback
        return self.split_to_list(v, delimiter)

    def get_abs_path(
        self, option: str, section: str, root_dir: str | None = None, create_dir: bool = False, fallback: Any = None
    ) -> str | None:
        """Get an absolute path from a configuration option.

        Parameters
        ----------
        option : str
            Option name
        section : str
            Section name
        root_dir : _type_, optional
            If given, relative paths are joined with this root directory, by default None
        create_dir : bool, optional
            If True, the directory is created if it does not exist, by default False
        fallback : _type_, optional
            Fallback value, by default None

        Returns
        -------
        str | None
            The absolute path
        """
        path = self.get(section, option, fallback=fallback)
        if path is None:
            return None

        if not os.path.isabs(path) and root_dir is not None:
            path = os.path.join(root_dir, path)

        n_path = os.path.normpath(path)
        a_path = os.path.abspath(n_path)

        if create_dir:
            if not os.path.exists(a_path):
                os.makedirs(a_path, exist_ok=True)

        return a_path
