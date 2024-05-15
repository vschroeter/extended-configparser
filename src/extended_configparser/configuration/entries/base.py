from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Generic
from typing import TypeVar

if TYPE_CHECKING:
    from extended_configparser import ExtendedConfigParser
    from extended_configparser.configuration.configuration import Configuration
    from extended_configparser.configuration.entries.confirmation import (
        ConfigConfirmationEntry,
    )

logger = logging.getLogger(__name__)

# Type alias for bool or callable
InquireCondition = bool | Callable[[], bool]

T = TypeVar("T")


class ConfigEntryCollection:
    """
    Super class for grouping ConfigEntries together.

    If you want to structure your configuration entries in a configuration class by grouping entries together in another data class,
    inherit from this class and define your entries as attributes of type ConfigEntry or ConfigEntryCollection.
    """

    pass


class ConfigEntry(Generic[T]):
    """
    Represents a single configuration entry.
    """

    def __init__(
        self,
        section: str,
        option: str,
        default: T | str,
        message: str,
        inquire: InquireCondition = True,
        is_dir: bool = False,
        value_getter: Callable[[str], T] = lambda x: x,
        value_setter: Callable[[T | str], str] = lambda x: str(x),
        **inquirer_kwargs,
    ) -> None:
        """Create a new ConfigEntry.

        Add additional kwargs to be passed to the inquirer prompt.

        Parameters
        ----------
        section : str
            Section name.
        option : str
            Option name.
        default : T
            Default value.
        message : str
            Message to be asked to the user for configurating this entry.
        inquire : bool, optional
            If the entry should be inquired to the user, by default True
        is_dir : bool, optional
            If the value is a dir path. If True, the directory of the path will be created when fetching the value if it does not exist.
        value_getter : Callable[[str], T], optional
            A function to transform the string entry value to your desired type
        value_setter : Callable[[T], str], optional
            A function to transform your logical value to the config string
        """

        self.section = self.escape_whitespace(section)
        """Section of the entry"""

        self.option = self.escape_whitespace(option)
        """Option of the entry"""

        self.default = value_setter(default)
        """Default value of the entry"""

        self.message = message
        """Message to be asked when the entry is inquired"""

        # self.required = required

        self.configuration: Configuration | None = None
        """Reference to the source configuration"""

        self.configparser: ExtendedConfigParser | None = None
        """The ConfigParser instance to read and write the configuration"""

        self.inquirer_kwargs = inquirer_kwargs
        """Additional kwargs to be passed to the inquirer prompt"""

        self._do_inquire = inquire
        """Set to True if the entry should be inquired to the user"""

        self.is_dir = is_dir
        """If the value is a dir. If True, the directory of the path will be created when fetching the value if it does not exist."""

        self.value_transformer = value_getter
        """A function to transform the string entry value to your desired type"""

        self.value_setter = value_setter
        """A function to transform your logical value to the config string"""

        if "qmark" not in self.inquirer_kwargs:
            self.inquirer_kwargs["qmark"] = "?"

        if "amark" not in self.inquirer_kwargs:
            self.inquirer_kwargs["amark"] = ">"

    def get_value_str(self) -> str:
        """Return the string representation of the entry for the value."""
        return f"{self.value}"

    def get_value(self, raw: bool = False):
        if self.configparser is None:
            raise ValueError("ConfigParser is not set.")

        return self.configparser.get(self.section, self.option, fallback=self.default, raw=raw)

    def set_value(self, value: T):
        if self.configparser is None:
            raise ValueError("ConfigParser is not set.")

        v = self.value_setter(value)
        self.configparser.set(self.section, self.option, v, self.get_comment())

        if self.configuration is not None and self.configuration.auto_save:
            self.configuration.write()

    @property
    def raw_value(self) -> str:
        return self.get_value(True)

    @property
    def value(self) -> T:
        v = self.get_value(False)
        if self.is_dir:
            from pathlib import Path

            p = Path(v)

            # TODO: Make this OS independent
            if p.is_absolute() or any(v.startswith(b) for b in ("./", "../", "~/")):
                # if not p.parent.exists():
                #     p.parent.mkdir(parents=True)
                if not p.exists():
                    try:
                        p.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        logger.warning(f"Failed to create directory {p}: {e}")

                v = str(p)

        # if self.value_transformer:
        v = self.value_transformer(v)
        return v

    @value.setter
    def value(self, value: T) -> None:
        self.set_value(value)

    def __str__(self) -> str:
        return f"{self.section}:{self.option} = {self.value if self.configparser else 'n/a'}"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def escape_whitespace(value: str) -> str:
        return re.sub(r"/s", "_", value).strip("_")

    @staticmethod
    def get_msg(msg: str, strip: str = ":.", end: str = ":") -> str:
        msg = msg.strip()
        msg = msg.strip(strip) + end
        return msg

    def do_inquire(self) -> bool:
        if isinstance(self._do_inquire, bool):
            return self._do_inquire
        elif callable(self._do_inquire):
            return self._do_inquire()

        return False

    def inquire(self, use_existing_as_default: bool = True) -> None:
        """Inquire the user for the value of this entry.

        Parameters
        ----------
        use_existing_as_default : bool, optional
            If True, the existing value of a config is taken as default value when asking the user, otherwise take the given default value, by default True
        """

        if not self.do_inquire():
            return

        from InquirerPy import inquirer

        msg = self.get_msg(self.message)
        self.value = inquirer.text(
            message=msg,
            default=(self.raw_value if use_existing_as_default else self.default),
            **self.inquirer_kwargs,
        ).execute()

    def get_comment(self) -> str:
        s = self.message
        if "instruction" in self.inquirer_kwargs:
            s += f"\nInstruction: {self.inquirer_kwargs['instruction']}"
        if "long_instruction" in self.inquirer_kwargs:
            s += f"\nLong Instruction: {self.inquirer_kwargs['long_instruction']}"

        return s
