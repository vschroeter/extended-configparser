from __future__ import annotations

import io
import pathlib

import pytest

from extended_configparser.configuration.configuration import Configuration
from extended_configparser.configuration.entries.base import ConfigEntry
from extended_configparser.configuration.entries.base import ConfigEntryCollection
from extended_configparser.configuration.entries.confirmation import (
    ConfigConfirmationEntry,
)
from extended_configparser.configuration.entries.section import ConfigSection
from extended_configparser.configuration.entries.selection import ConfigSelectionEntry


class MainConfigPaths(ConfigEntryCollection):
    def __init__(self):
        section = ConfigSection("Dirs")
        self.data_root_dir = section.Option(
            "data_root_dir",
            r"${HOME}/test/",
            "Root directory for all data",
            long_instruction="This is a longer description of what you have to do.",
        )

        subdir_section = ConfigSection("Subdirs")
        self.sub_dir = subdir_section.Option("sub_dir", r"${Dirs:data_root_dir}/subdir/", "Main subdirectory.")


class MainConfig(Configuration):
    def __init__(self, path: str):
        super().__init__(path)
        self.paths = MainConfigPaths()
        self.test = ConfigEntry("Test", "Foo", "Bla", "Test entry")

        self.confirmation = ConfigConfirmationEntry("Test", "Confirmation", False, "Test confirmation entry")

        self.selection = ConfigSelectionEntry(
            "Test",
            "Selection",
            ["b"],
            "Test selection entry",
            choices=["a", "b", "c"],
            multiselect=True,
            delimiter=",\n",
        )


# TODO: Automate the input for testing. Currently it is manual.
def inquire(shared_datadir):

    config = MainConfig(shared_datadir / "test_config.cfg")

    # mocker.patch("builtins.input", side_effect=["/tmp/test", "/tmp/test/subdir", "TestValue"])
    # mocker.patch("sys.stdin", side_effect=["/tmp/test", "/tmp/test/subdir", "TestValue"])
    # monkeypatch.setattr('sys.stdin', io.StringIO('my input'))
    config.inquire()
    config.write()

    content = (shared_datadir / "test_config.cfg").read_text()
    print(content)
    s = """[Dirs]
# Root directory for all data
# Long Instruction: This is a longer description of what you have to do.
data_root_dir = ${HOME}/test/

[Subdirs]
# Main subdirectory.
sub_dir = ${Dirs:data_root_dir}/subdir/

[Test]
# Test entry
foo = Bla
# Test confirmation entry
confirmation = Yes
# Test selection entry
selection = a,
        b,
        c
"""
    assert content.strip() == s.strip()


if __name__ == "__main__":
    path = pathlib.Path(__file__).parent / "tmp"
    # If path exists, delete all files in the dir
    if path.exists():
        for f in path.iterdir():
            f.unlink()

    inquire(path)
