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
        path: str | None,
        interpolation: Interpolation = EnvInterpolation(),
        base_paths: list[str] | None = None,
        auto_save: bool = False,
    ) -> None:
        """Create a new Configuration object.

        Parameters
        ----------
        path : str | None
            File path to the configuration file.
            You can leave the path to None if the config is mainly used to read values and you provide base_paths to read from.
            In this case, the write method needs a save_path to write the configuration.
        interpolation : Interpolation, optional
            Interpolation to use for the configuration file, by default EnvInterpolation()
        base_paths : list[str] | None, optional
            If the values of the configuration using interpolation reference other configuration files, those file paths can be specified here.
        auto_save : bool, optional
            If True, the configuration will be saved automatically after setting a value.
        """

        self.config_path: str | None = path
        """File path to the configuration file."""

        self.auto_save = auto_save if path is not None else False
        """If True, the configuration will be saved automatically after setting a value."""

        self.base_paths = base_paths or []
        """Paths to other configuration files that are automatically read."""

        self._entries: list[ConfigEntry] = []
        """Cache for the entries of the configuration."""

        self._config_parser = ExtendedConfigParser(interpolation=interpolation)
        """ConfigParser object used to read and write the configuration file."""

        self._update_entries()

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

    def _update_entries(self):
        """Update the entries based on the current read configurations."""
        auto_save = self.auto_save
        self.auto_save = False

        for entry in self.entries:
            entry.configparser = self._config_parser
            entry.configuration = self
            entry.value = entry.raw_value or entry.default
        self.auto_save = auto_save

    def load(self, inquire_if_missing: bool = False, quiet: bool = False) -> None:
        """Load the configuration file and set the values of the entries.

        Parameters
        ----------
        inquire_if_missing : bool, optional
            If True, the user will be asked to provide the values for the configuration entries.
        quiet : bool, optional
            If True, no warning will be printed if the configuration file is missing.
        """

        for base_path in self.base_paths:
            if not os.path.exists(base_path):
                if not quiet:
                    logger.warning(f"Base configuration file {base_path} not found.")
                continue

            self._config_parser.read(base_path)

        if self.config_path is not None:
            if not os.path.exists(self.config_path):
                if not quiet:
                    logger.warning(f"Configuration file {self.config_path} not found.")
                if inquire_if_missing:
                    self.inquire()
            else:
                self._config_parser.read(self.config_path)

        self._update_entries()

    def read(self, path: str | list[str]) -> list[str]:
        """Read the configuration from the file path."""

        paths_ok = self._config_parser.read(path)
        self._update_entries()
        return paths_ok

    def write(self, save_path: str | None = None) -> None:
        """Write the configuration to the file path.

        Parameters
        ----------
        save_path : str | None, optional
            If given, the configuration will be written to this path instead of the default one. Must be provided if the configuration has no default path.
        """
        if save_path is None:
            if self.config_path is None:
                raise ValueError("No save path provided and no default path set.")
            save_path = self.config_path

        # Check if the directory exists
        if not os.path.exists(os.path.dirname(save_path)):
            os.makedirs(os.path.dirname(save_path))

        # We cannot just write the config file, as there could be base configs, whose content should not appear in this config.
        parser = ExtendedConfigParser()
        if os.path.exists(save_path):
            parser.read(save_path)
        for entry in self.entries:
            parser.set(entry.section, entry.option, entry.raw_value or entry.default, entry.get_comment())

        with io.open(save_path, "w") as f:
            parser.write(f)

    def inquire(self, use_existing_values: bool = True) -> None:
        """Inquire the user for the values of the entries."""

        logger.debug(f"Inquire configuration @ {self.config_path}")
        self.load(quiet=True)
        for entry in self.entries:
            entry.inquire(use_existing_values)
            # self._set_entry(entry)

        logger.debug(f"Configuration of {self.config_path} completed.")

    def __getitem__(self, key: str) -> SectionProxy:
        """Returns the section with the given key."""
        return self._config_parser[key]
