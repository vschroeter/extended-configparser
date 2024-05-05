from __future__ import annotations

import logging
import os
from configparser import Interpolation

from extended_configparser.configuration.entries import ConfigEntry
from extended_configparser.configuration.entries import ConfigEntryCollection
from extended_configparser.interpolator import EnvInterpolation
from extended_configparser.parser import ExtendedConfigParser

logger = logging.getLogger(__name__)


class Configuration:
    """
    Super class for custom Configuration classes representing a configuration file in ini format.

    In your subclass, define your entries as attributes of type ConfigEntry or ConfigEntryCollection.
    Those defined entries will be read from and written to the configuration file.
    With `inqure()` the user will be asked to provide the values for the defined entries.
    """

    def __init__(self, path: str, interpolation: Interpolation = EnvInterpolation()) -> None:
        self.config_path = path

        self._entries: list[ConfigEntry] = []
        self._config_parser = ExtendedConfigParser(interpolation=interpolation)

    @staticmethod
    def get_config_entries_in_object(cfg: Configuration, ignore: list[str] = ["entries"]) -> list[ConfigEntry]:
        """
        Get all ConfigEntries in the given object.
        Members in the ignore list will be skipped.
        """
        entries: list[ConfigEntry] = []
        for attr in cfg.__dict__:
            if attr in ignore:
                continue

            if isinstance(getattr(cfg, attr), ConfigEntry):
                entries.append(getattr(cfg, attr))
            elif isinstance(getattr(cfg, attr), ConfigEntryCollection):
                entries.extend(Configuration.get_config_entries_in_object(getattr(cfg, attr)))

        return entries

    @property
    def entries(self) -> list[ConfigEntry]:
        if len(self._entries) == 0:
            # Iter over each attribute of the object and check if it is a ConfigEntry or a subclass of it
            self._entries = Configuration.get_config_entries_in_object(self)

        return self._entries

    def load(self, inquire_if_missing: bool = False) -> None:
        """Load the configuration file and set the values of the entries.


        Parameters
        ----------
        inquire_if_missing : bool, optional
            If True, the user will be asked to provide the values for the configuration entries.

        Raises
        ------
        ValueError
            If a required option is missing and use_default_for_missing_options is False
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file {self.config_path} not found.")
            if inquire_if_missing:
                self.inquire()
        else:
            self._config_parser.read(self.config_path)

        for entry in self.entries:
            entry.configparser = self._config_parser
            entry.value = entry.raw_value

    def write(self) -> None:
        """Write the configuration to the file path."""
        # Check if the directory exists
        if not os.path.exists(os.path.dirname(self.config_path)):
            os.makedirs(os.path.dirname(self.config_path))

        with open(self.config_path, "w") as f:
            self._config_parser.write(f)

    def inquire(self) -> None:
        """Inquire the user for the values of the entries."""

        logger.debug(f"Configuring @ {self.config_path}")
        self.load()
        for entry in self.entries:
            entry.inquire()
            # self._set_entry(entry)

        logger.debug(f"Configuration of {self.config_path} completed.")
