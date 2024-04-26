from __future__ import annotations

import os

import pytest
from pytest import fixture

from extended_configparser.interpolator import EnvInterpolation
from extended_configparser.parser import ExtendedConfigParser

DELIMITER = ["=", ":"]
COMMENT_PREFIXES = ["#", ";"]


def test_write(shared_datadir, tmp_path):
    contents = (shared_datadir / "env_config.cfg").read_text()

    parser = ExtendedConfigParser()
    parser.read_string(contents)

    output_path = tmp_path / "output.cfg"
    with open(output_path, "w") as f:
        parser.write(f)

    output_contents = output_path.read_text()

    assert contents.strip() == output_contents.strip()


def test_interpolation(shared_datadir, tmp_path):
    contents = (shared_datadir / "env_config.cfg").read_text()

    os.environ["TEMP_ENV_VAR1"] = "EnvValue1"
    os.environ["TEMP_ENV_VAR2"] = "EnvValue2"

    parser = ExtendedConfigParser(interpolation=EnvInterpolation())
    parser.read_string(contents)

    assert parser.get("Section1", "a") == "a"
    assert parser.get("Section1", "b") == "a"
    assert parser.get("Section1", "c") == "EnvValue1/a"
    assert parser.get("Section1", "d") == "EnvValue2"
    assert parser.get("Section2", "a") == "a"
    assert parser.get("Section2", "b") == "EnvValue2/a/EnvValue1"

    assert parser.get("Section2", "b", raw=True) == r"$TEMP_ENV_VAR2/${Section1:b}/${TEMP_ENV_VAR1}"
