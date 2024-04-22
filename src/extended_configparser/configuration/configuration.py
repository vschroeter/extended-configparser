from __future__ import annotations
import os

from typing import TYPE_CHECKING

from extended_configparser.configuration.entries import ConfigEntry, ConfigEntryCollection
from extended_configparser.interpolator import EnvInterpolation
from extended_configparser.parser import ExtendedConfigParser

if TYPE_CHECKING:
    from InquirerPy.utils import InquirerPyValidate

import logging

logger = logging.getLogger(__name__)


class Configuration:
    """
    Super class for custom Configuration classes representing a configuration file in ini format.

    In your subclass, define your entries as attributes of type ConfigEntry or ConfigEntryCollection.
    Those defined entries will be read from and written to the configuration file.
    With `inqure()` the user will be asked to provide the values for the defined entries.
    """

    def __init__(self, path: str = None, interpolation=EnvInterpolation()):
        self.config_path = path

        self._entries: list[ConfigEntry] = None
        self._config_parser = ExtendedConfigParser(interpolation=interpolation)

    @staticmethod
    def get_config_entries_in_object(obj, ignore=["entries"]):
        """
        Get all ConfigEntries in the given object.
        Members in the ignore list will be skipped.
        """
        entries: list[ConfigEntry] = []
        for attr in obj.__dict__:
            if attr in ignore:
                continue

            if isinstance(getattr(obj, attr), ConfigEntry):
                entries.append(getattr(obj, attr))
            elif isinstance(getattr(obj, attr), ConfigEntryCollection):
                entries.extend(Configuration.get_config_entries_in_object(getattr(obj, attr)))

        return entries

    @property
    def entries(self) -> list[ConfigEntry]:
        if self._entries is None or len(self._entries) == 0:
            # Iter over each attribute of the object and check if it is a ConfigEntry or a subclass of it
            self._entries = Configuration.get_config_entries_in_object(self)

        return self._entries

    def load(self, use_default_for_missing_options: bool = True, inquire_if_missing: bool = False):
        """Load the configuration file and set the values of the entries.


        Parameters
        ----------
        use_default_for_missing_options : bool, optional
            If True, a missing option in the read configfile will be set to its default. Otherwise, raise a ValueError. By default True

        Raises
        ------
        ValueError
            If a required option is missing and use_default_for_missing_options is False
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file {self.config_path} not found. Creating new configuration file.")
            if inquire_if_missing:
                self.inquire()
            self.write()
            return

        self._config_parser.read(self.config_path)

        for entry in self.entries:
            if entry.required and not self._config_parser.has_option(entry.section, entry.option):
                if use_default_for_missing_options:
                    entry.value = entry.default
                    continue

                raise ValueError(
                    f"Required option {entry.option} not found in section {entry.section} for configuration {self.config_path}"
                )
            entry.value = self._config_parser.get(entry.section, entry.option, fallback=entry.default, raw=True)

    def write(self):
        """Write the configuration to the file path."""
        for entry in self.entries:
            self._set_entry(entry)

        # Check if the directory exists
        if not os.path.exists(os.path.dirname(self.config_path)):
            os.makedirs(os.path.dirname(self.config_path))

        with open(self.config_path, "w") as f:
            self._config_parser.write(f)

    def _set_entry(self, entry: ConfigEntry):
        """Set the value of the entry in the configuration parser.

        Parameters
        ----------
        entry : ConfigEntry
            The entry to set.
        """
        if not self._config_parser.has_section(section=entry.section):
            self._config_parser.add_section(section=entry.section)

        self._config_parser.set(entry.section, entry.option, entry.value, entry.get_comment())

    def inquire(self):
        """Inquire the user for the values of the entries."""

        logger.debug(f"Configuring @ {self.config_path}")
        self.load()
        for entry in self.entries:
            entry.inquire()
            self._set_entry(entry)

        self.write()
        self.load()
        logger.debug("Configuration of {self.config_path} completed.")
