from __future__ import annotations

import logging
from typing import Callable
from typing import TypeVar

from extended_configparser.configuration.entries.base import ConfigEntry
from extended_configparser.configuration.entries.base import InquireCondition
from extended_configparser.configuration.entries.confirmation import (
    ConfigConfirmationEntry,
)
from extended_configparser.configuration.entries.selection import ConfigSelectionEntry

logger = logging.getLogger(__name__)


S = TypeVar("S")


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
        default: S | str | None,
        message: str,
        inquire: InquireCondition = True,
        is_dir: bool = False,
        value_getter: Callable[[str], S] = lambda x: x,
        value_setter: Callable[[S | str], str] = lambda x: str(x),
        **inquirer_kwargs,
    ) -> ConfigEntry[S]:
        """Create a ConfigEntry for that section with the given parameters."""
        return ConfigEntry[S](
            section=self.name,
            option=option,
            default=default,
            message=message,
            inquire=inquire,
            is_dir=is_dir,
            value_getter=value_getter,
            value_setter=value_setter,
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

    def SelectionOption(
        self,
        section: str,
        option: str,
        default: list[str],
        message: str,
        inquire: InquireCondition = True,
        choices: list[str] = [],
        multiselect: bool = False,
        delimiter: str = ", ",
        **inquirer_kwargs,
    ) -> ConfigSelectionEntry:
        """Create a ConfigEntry for that section with the given parameters."""
        return ConfigSelectionEntry(
            section=section,
            option=option,
            default=default,
            message=message,
            inquire=inquire,
            choices=choices,
            multiselect=multiselect,
            delimiter=delimiter,
            **inquirer_kwargs,
        )
