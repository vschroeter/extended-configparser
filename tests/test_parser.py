from __future__ import annotations

import pytest
from pytest import fixture

from extended_configparser.parser import ExtendedConfigParser

DELIMITER = ["=", ":"]
COMMENT_PREFIXES = ["#", ";"]


def test_read(shared_datadir):
    contents = (shared_datadir / "config1.cfg").read_text()

    parser = ExtendedConfigParser()
    print(contents)
    parser.read_string(contents)

    assert len(parser.sections()) == 1

    top_comment = "Top Comment 1\nTop Comment 2"
    assert parser.top_comment == top_comment
    end_comment = "End of file comment"
    assert parser.end_comment == end_comment

    section_a_comment = "Section Comment"
    assert parser.get_comment("Section.A") == section_a_comment

    option1_comment = "Single line comment"
    assert parser.get_comment("Section.A", "Option1") == option1_comment

    option2_comment = "Multiline\ncomment"
    assert parser.get_comment("Section.A", "Option2") == option2_comment


def test_write(shared_datadir, tmp_path):
    contents = (shared_datadir / "config1.cfg").read_text()
    result = (shared_datadir / "config1_result.cfg").read_text()

    parser = ExtendedConfigParser()
    parser.read_string(contents)

    output_path = tmp_path / "output.cfg"
    with open(output_path, "w") as f:
        parser.write(f)

    output_contents = output_path.read_text()

    output_lines = output_contents.split("\n")
    result_lines = result.split("\n")

    output_lines = [line.strip() for line in output_lines if len(line.strip()) > 0]
    result_lines = [line.strip() for line in result_lines if len(line.strip()) > 0]

    assert len(output_lines) == len(result_lines)
    for output_line, result_line in zip(output_lines, result_lines):
        assert output_line.strip() == result_line.strip()


def test_str(shared_datadir, tmp_path):
    contents = (shared_datadir / "config1.cfg").read_text()
    result = (shared_datadir / "config1_result.cfg").read_text()

    parser = ExtendedConfigParser()
    parser.read_string(contents)

    output_path = tmp_path / "output.cfg"
    with open(output_path, "w") as f:
        parser.write(f)

    output_contents = output_path.read_text()
    output_str = str(parser)

    assert output_contents.strip() == output_str.strip()


def test_change_comment(shared_datadir, tmp_path):
    contents = (shared_datadir / "config1.cfg").read_text()
    result = (shared_datadir / "config2_result.cfg").read_text()

    parser = ExtendedConfigParser()
    parser.read_string(contents)

    parser.add_section("Section.New", "New Section")
    parser.set("Section.New", "new_option", "new_value", "New value with new comment")

    parser.set_comment("Section.A", comment="New Section Comment")
    parser.set_comment("Section.A", "option2", comment="New option2 comment")

    output_path = tmp_path / "output.cfg"
    with open(output_path, "w") as f:
        parser.write(f)

    output_contents = output_path.read_text()

    output_lines = output_contents.split("\n")
    result_lines = result.split("\n")

    output_lines = [line.strip() for line in output_lines if len(line.strip()) > 0]
    result_lines = [line.strip() for line in result_lines if len(line.strip()) > 0]

    print(output_lines)
    print(result_lines)

    assert len(output_lines) == len(result_lines)
    for output_line, result_line in zip(output_lines, result_lines):

        assert output_line.strip() == result_line.strip()
