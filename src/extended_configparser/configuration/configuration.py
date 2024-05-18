from __future__ import annotations

import io
import logging
import os
from configparser import Interpolation
from configparser import SectionProxy

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

    def __init__(
        self,
        path: str,
        interpolation: Interpolation = EnvInterpolation(),
        base_paths: list[str] | None = None,
        auto_save: bool = False,
    ) -> None:
        """Create a new Configuration object.

        Parameters
        ----------
        path : str
            File path to the configuration file.
        interpolation : Interpolation, optional
            Interpolation to use for the configuration file, by default EnvInterpolation()
        base_paths : list[str] | None, optional
            If the values of the configuration using interpolation reference other configuration files, those file paths can be specified here.
        auto_save : bool, optional
            If True, the configuration will be saved automatically after setting a value.
        """

        self.config_path = path
        """File path to the configuration file."""

        self.auto_save = auto_save
        """If True, the configuration will be saved automatically after setting a value."""

        self.base_paths = base_paths or []
        """Paths to other configuration files that are automatically read."""

        self._entries: list[ConfigEntry] = []
        """Cache for the entries of the configuration."""

        self._config_parser = ExtendedConfigParser(interpolation=interpolation)
        """ConfigParser object used to read and write the configuration file."""

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
        """
        Get all ConfigEntries in the configuration object.
        Based on the defined ConfigEntrie or ConfigEntryCollection members of the object.
        """

        if len(self._entries) == 0:
            # Iter over each attribute of the object and check if it is a ConfigEntry or a subclass of it
            self._entries = Configuration.get_config_entries_in_object(self)

        return self._entries

    def load(self, inquire_if_missing: bool = False, quiet: bool = False) -> None:
        """Load the configuration file and set the values of the entries.


        Parameters
        ----------
        inquire_if_missing : bool, optional
            If True, the user will be asked to provide the values for the configuration entries.
        quiet : bool, optional
            If True, no warning will be printed if the configuration file is missing.

        Raises
        ------
        ValueError
            If a required option is missing and use_default_for_missing_options is False
        """

        for base_path in self.base_paths:
            if not os.path.exists(base_path):
                logger.warning(f"Base configuration file {base_path} not found.")
                continue

            self._config_parser.read(base_path)

        if not os.path.exists(self.config_path):
            if not quiet:
                logger.warning(f"Configuration file {self.config_path} not found.")
            if inquire_if_missing:
                self.inquire()
        else:
            self._config_parser.read(self.config_path)

        auto_save = self.auto_save
        self.auto_save = False

        for entry in self.entries:
            entry.configparser = self._config_parser
            entry.configuration = self
            entry.value = entry.raw_value

        self.auto_save = auto_save

    def write(self) -> None:
        """Write the configuration to the file path."""
        # Check if the directory exists
        if not os.path.exists(os.path.dirname(self.config_path)):
            os.makedirs(os.path.dirname(self.config_path))

        # We cannot just write the config file, as there could be base configs, whose content should not appear in this config.
        parser = ExtendedConfigParser()
        if os.path.exists(self.config_path):
            parser.read(self.config_path)
        for entry in self.entries:
            parser.set(entry.section, entry.option, entry.raw_value, entry.get_comment())

        with io.open(self.config_path, "w") as f:
            # self._config_parser.write(f)
            parser.write(f)

    def inquire(self, use_existing_values: bool = True) -> None:
        """Inquire the user for the values of the entries."""

        logger.debug(f"Configuring @ {self.config_path}")
        self.load(quiet=True)
        for entry in self.entries:
            entry.inquire(use_existing_values)
            # self._set_entry(entry)

        logger.debug(f"Configuration of {self.config_path} completed.")

    def __getitem__(self, key: str) -> SectionProxy:
        """Returns the section with the given key."""
        return self._config_parser[key]
