from __future__ import annotations

import logging

from extended_configparser.configuration.entries.base import ConfigEntry
from extended_configparser.configuration.entries.base import InquireCondition
from extended_configparser.configuration.entries.confirmation import (
    ConfigConfirmationEntry,
)

logger = logging.getLogger(__name__)


class ConfigSection:
    """
    Helper class to group ConfigEntries together under a section.
    Create entries by calling `section.ConfigSection("section_name")`.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def Option(
        self,
        option: str,
        default: str,
        message: str,
        inquire: InquireCondition = True,
        **inquirer_kwargs,
    ) -> ConfigEntry:
        """Create a ConfigEntry for that section with the given parameters."""
        return ConfigEntry(
            section=self.name,
            option=option,
            default=default,
            message=message,
            inquire=inquire,
            **inquirer_kwargs,
        )

    def ConfirmationOption(
        self,
        option: str,
        default: bool,
        message: str,
        inquire: InquireCondition = True,
        **inquirer_kwargs,
    ) -> ConfigConfirmationEntry:
        """Create a ConfigConfirmationEntry for that section with the given parameters."""

        return ConfigConfirmationEntry(
            section=self.name,
            option=option,
            default=default,
            message=message,
            inquire=inquire,
            **inquirer_kwargs,
        )
