from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class ConfigEntryCollection:
    """
    Super class for grouping ConfigEntries together.

    If you want to structure your configuration entries in a configuration class by grouping entries together in another data class,
    inherit from this class and define your entries as attributes of type ConfigEntry or ConfigEntryCollection.
    """

    pass


class ConfigSection:
    """
    Helper class to group ConfigEntries together under a section.
    Create entries by calling `section.ConfigSection("section_name")`.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def ConfigOption(self, option: str, default: str, message: str, required: bool = True, **inquirer_kwargs) -> ConfigEntry:
        """Create a ConfigEntry for that section with the given parameters."""
        return ConfigEntry(
            section=self.name,
            option=option,
            default=default,
            message=message,
            required=required,
            **inquirer_kwargs,
        )


class ConfigEntry:
    """
    Represents a single configuration entry.
    """

    def __init__(
        self,
        section: str,
        option: str,
        default: str,
        message: str,
        required: bool = True,
        inquire: bool = True,
        use_existing_as_default=True,
        **inquirer_kwargs,
    ) -> None:
        """Create a new ConfigEntry.

        Parameters
        ----------
        section : str
            Section name.
        option : str
            Option name.
        default : str
            Default value.
        message : str
            Message to be asked to the user for configurating this entry.
        required : bool, optional
            If the entry is required, by default True
        inquire : bool, optional
            If the entry should be inquired to the user, by default True
        use_existing_as_default : bool, optional
            If True, the existing value of a config is taken as default value when asking the user, otherwise take the given default value, by default True
        """
        self.section = self.escape_whitespace(section)
        self.option = self.escape_whitespace(option)
        self.default = default
        self.message = message
        self.required = required
        self.value: str | None = default
        self.use_existing_as_default = use_existing_as_default
        self.inquirer_kwargs = inquirer_kwargs
        self.do_inquire = inquire

        if "qmark" not in self.inquirer_kwargs:
            self.inquirer_kwargs["qmark"] = "?"

        if "amark" not in self.inquirer_kwargs:
            self.inquirer_kwargs["amark"] = ">"

    def __str__(self) -> str:
        return f"{self.section}:{self.option} = {self.value}"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def escape_whitespace(value: str) -> str:
        return value.replace(" ", "_")

    def inquire(self) -> None:
        """Inquire the user for the value of this entry."""

        if not self.do_inquire:
            return

        from InquirerPy import inquirer

        msg = self.message.strip()
        msg = msg.strip(".:") + ":"
        self.value = inquirer.text(
            message=msg,
            default=(self.value if self.use_existing_as_default else self.default),
            **self.inquirer_kwargs,
        ).execute()

    def get_comment(self) -> str:
        s = self.message
        if "instruction" in self.inquirer_kwargs:
            s += f"\nInstruction: {self.inquirer_kwargs['instruction']}"
        if "long_instruction" in self.inquirer_kwargs:
            s += f"\nLong Instruction: {self.inquirer_kwargs['long_instruction']}"

        return s
