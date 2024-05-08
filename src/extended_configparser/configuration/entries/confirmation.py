from __future__ import annotations

import logging
from typing import Any

from extended_configparser.configuration.entries.base import ConfigEntry
from extended_configparser.configuration.entries.base import InquireCondition

logger = logging.getLogger(__name__)


class ConfigConfirmationEntry(ConfigEntry):
    """
    Represents a single confirmation configuration entry (yes/no).
    """

    def __init__(
        self,
        section: str,
        option: str,
        default: bool,
        message: str,
        inquire: InquireCondition = True,
        **inquirer_kwargs,
    ) -> None:
        """Create a new ConfigConfirmationEntry.

        Parameters
        ----------
        section : str
            Section name.
        option : str
            Option name.
        default : bool
            Default value.
        message : str
            Message to be asked to the user for configurating this entry.
        """
        super().__init__(
            section=section,
            option=option,
            default=default,
            message=message,
            inquire=inquire,
            **inquirer_kwargs,
        )

    def inquire(self, use_existing_as_default: bool = True) -> None:
        """Inquire the user for the value of this entry."""

        if not self.do_inquire():
            return

        from InquirerPy import inquirer

        msg = self.get_msg(self.message)
        self.value = inquirer.confirm(
            message=msg,
            default=(self.to_bool(self.value) if use_existing_as_default else self.default),
            **self.inquirer_kwargs,
        ).execute()

    @staticmethod
    def to_bool(value: Any):
        """Transform values to boolean."""

        if value is None:
            return False

        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            if value > 0:
                return True

        if isinstance(value, str):
            v = value.lower()
            if v == "true" or v == "yes" or v == "1":
                return True

            return False

        try:
            return bool(value)
        except:
            return False

    @staticmethod
    def get_bool_str(value: bool) -> str:
        return "Yes" if value else "No"

    @property
    def value(self):
        return self.to_bool(self.get_value())

    @value.setter
    def value(self, value: Any):
        self.set_value(self.get_bool_str(self.to_bool(value)))
