from __future__ import annotations
import os

from InquirerPy import inquirer

from typing import TYPE_CHECKING

from extended_configparser.configuration.entries import ConfigEntry, ConfigEntryCollection
from extended_configparser.interpolator import EnvInterpolation
from extended_configparser.parser import ExtendedConfigParser

if TYPE_CHECKING:
    from InquirerPy.utils import InquirerPyValidate

import logging

logger = logging.getLogger(__name__)


class Configuration:
    def __init__(self, path: str = None, interpolation=EnvInterpolation()):

        self._entries: list[ConfigEntry] = None

        self.config_path = os.path.abspath(path)
        self._config_parser = ExtendedConfigParser(interpolation=interpolation)

    @staticmethod
    def get_config_entries_in_object(obj, ignore=["entries"]):
        entries: list[ConfigEntry] = []
        for attr in obj.__dict__:
            if attr == "entries":
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

    def read(self, use_default_values: bool = True):
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file {self.config_path} not found. Creating new configuration file.")
            self.write()
            return

        self._config_parser.read(self.config_path)

        for entry in self.entries:
            if entry.required and not self._config_parser.has_option(entry.section, entry.option):
                if use_default_values:
                    entry.value = entry.default
                    continue

                raise ValueError(
                    f"Required option {entry.option} not found in section {entry.section} for configuration {self.config_path}"
                )
            entry.value = self._config_parser.get(entry.section, entry.option, fallback=entry.default, raw=True)

    def write(self):
        for entry in self.entries:
            self.set_entry(entry)

        with open(self.config_path, "w") as f:
            self._config_parser.write(f)

    def set_entry(self, entry: ConfigEntry):
        if not self._config_parser.has_section(section=entry.section):
            self._config_parser.add_section(section=entry.section)

        self._config_parser.set(entry.section, entry.option, entry.value, entry.get_comment())

    def inquire(self):
        logger.debug(f"Configuring @ {self.config_path}")
        self.read()
        for entry in self.entries:
            entry.inquire()
            self.set_entry(entry)

        self.write()
        self.read()
        logger.debug("Configuration of {self.config_path} completed.")
