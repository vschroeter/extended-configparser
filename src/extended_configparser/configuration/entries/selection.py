from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from extended_configparser.configuration.entries.base import ConfigEntry
from extended_configparser.configuration.entries.base import InquireCondition

logger = logging.getLogger(__name__)


class ConfigSelectionEntry(ConfigEntry[str]):
    """
    Represents a selection configuration entry with a list of selectable options.
    """

    def __init__(
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
    ) -> None:
        """Create a new ConfigSelectionEntry.

        Parameters
        ----------
        section : str
            Section name.
        option : str
            Option name.
        default : list[str]
            Default values.
        message : str
            Message to be asked to the user for configurating this entry.
        inquire : bool, optional
            If the entry should be inquired, by default True
        choices : list[str], optional
            List of choices.
        multiselect : bool, optional
            If multiple choices can be selected, by default False
        list_delimiter : str, optional
            Delimiter for the list values, by default ", "
        """
        super().__init__(
            section=section,
            option=option,
            default=self.list_to_string(default),
            message=message,
            inquire=inquire,
            **inquirer_kwargs,
        )

        self.choices = choices
        self.multiselect = multiselect
        self.delimiter = delimiter

    def inquire(self, use_existing_as_default: bool = True) -> None:
        """Inquire the user for the value of this entry."""

        if not self.do_inquire:
            return

        from InquirerPy import inquirer
        from InquirerPy.base import Choice

        msg = self.get_msg(self.message)
        values = set(self.value)
        choices = [Choice(i, enabled=i in values) for i in self.choices]

        kwargs = self.inquirer_kwargs.copy()
        if "long_instruction" not in kwargs:
            kwargs["long_instruction"] = "Use <tab> to de/select values and <enter> to confirm."

        result = inquirer.select(
            message=msg,
            choices=choices,
            multiselect=self.multiselect,
            default=None,
            **self.inquirer_kwargs,
        ).execute()

        self.value = result

    @staticmethod
    def list_to_string(values: list[str], delimiter: str = ", ") -> str:
        """Transform values to a list."""
        return delimiter.join(values)

    @staticmethod
    def string_to_list(value: str, delimiter: str = ", ") -> list[str]:
        """Transform a string to a list."""
        if value is None or value == "":
            return []
        return [v.strip() for v in value.split(delimiter)]

    @property
    def value(self) -> list[str]:
        return self.string_to_list(self.get_value(), self.delimiter)

    @value.setter
    def value(self, value: Any) -> None:
        self.set_value(self.list_to_string(value, self.delimiter))
